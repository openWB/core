"""Synchronous portal requests with a module-owned in-memory cache."""

import logging
import re
from typing import Optional

from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common import req
from modules.vehicles.vweuda.api import (
    ApiError, AuthError, DatasetError, EudaApiClient, NO_CONTENT_SUFFIX, brand_for_vin,
)
from modules.vehicles.vweuda.vehicle_data import dataset_time, number, parse_vehicle_data
from modules.vehicles.vweuda.config import VWEUDAConfiguration

log = logging.getLogger(__name__)


class EudaVehicle:
    """One cache shared by the updater and interval callback, without a worker."""

    def __init__(self, configuration: VWEUDAConfiguration, vehicle: int) -> None:
        self.configuration = configuration
        self.vehicle = vehicle
        self.vin = configuration.vin
        self.last_request_failed = False
        self._result: Optional[dict] = None
        self._processed: set[str] = set()

    def get_request_interval_override(self) -> Optional[float]:
        return 60 if self.last_request_failed else None

    def _merge(self, result: dict) -> bool:
        result = dict(result)
        for field in ("soc", "soc_timestamp", "range", "odometer"):
            result[field] = number(result.get(field))
        if result["soc"] is None or result["soc"] > 100 or not result["soc_timestamp"]:
            return False
        if self._result is not None:
            if result["soc_timestamp"] < self._result["soc_timestamp"]:
                return False
            if result["range"] is None:
                result["range"] = self._result.get("range")
            previous_odometer = self._result.get("odometer")
            if previous_odometer is not None:
                result["odometer"] = max(result["odometer"] or 0, previous_odometer)
        self._result = result
        return True

    def _poll(self, client: EudaApiClient) -> None:
        identifier = client.get_metadata(self.vin).get("Identifier")
        if not identifier:
            raise ApiError("Kontinuierlicher Datenabruf im Portal noch nicht bereit")
        listing = client.list_datasets(self.vin, identifier)
        content = sorted((entry for entry in listing
                          if entry.get("name") and not entry["name"].endswith(NO_CONTENT_SUFFIX)),
                         key=dataset_time, reverse=True)
        if not content:
            raise ApiError("Im Portal sind noch keine Datenpakete mit Inhalt verfügbar")
        self._processed.intersection_update(entry["name"] for entry in content)
        for entry in content:
            name = entry["name"]
            if name in self._processed:
                continue
            try:
                _, payload = client.download_dataset(self.vin, identifier, name)
                if payload.get("vin") != self.vin:
                    raise ValueError("VIN mismatch")
                result = parse_vehicle_data(payload)
                if self._merge(result):
                    # SoC and timestamp suffice; optional values do not justify
                    # more downloads. Skip the remaining history on later polls.
                    self._processed.update(entry["name"] for entry in content)
                    return
            except (DatasetError, ValueError, TypeError, KeyError, AttributeError):
                log.warning("EUDA ev%s: Ungültiges Datenpaket übersprungen", self.vehicle)
            self._processed.add(name)

    def fetch(self, update: VehicleUpdateData) -> CarState:
        error_message = None
        try:
            conf = self.configuration
            if not conf.user_id or not conf.password:
                raise AuthError("SOCERR-01: Benutzername und Kennwort müssen konfiguriert sein")
            if not isinstance(self.vin, str) or not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", self.vin):
                raise ApiError("SOCERR-02: Bitte eine gültige 17-stellige VIN konfigurieren")
            # A fresh session per scheduled attempt is closed after the request.
            with req.get_http_session() as session:
                self._poll(EudaApiClient(session, conf.user_id, conf.password, brand_for_vin(self.vin)))
            if self._result is None:
                raise ApiError("Es wurden noch keine gültigen Fahrzeugdaten empfangen")
        except Exception as error:
            self.last_request_failed = True
            error_message = str(error)
            if isinstance(error, ApiError):
                log.warning("EUDA ev%s: Abruf fehlgeschlagen: %s", self.vehicle, error_message)
            else:
                log.exception("EUDA ev%s: Unerwarteter Fehler beim Abruf", self.vehicle)
            if self._result is None:
                raise ApiError(f"SOCERR-02: {error_message}") from error
        else:
            self.last_request_failed = False

        result = self._result
        range_km = result.get("range")
        if range_km is None:
            capacity, consumption = number(update.battery_capacity), number(update.average_consump)
            if capacity is not None and consumption is not None and consumption > 0:
                range_km = result["soc"] * capacity / consumption
        warning = result.get("warning")
        if error_message:
            message = f"EUDA-Abruf fehlgeschlagen; letzter gültiger Stand: {error_message}"
            warning = " ".join(filter(None, [warning, message]))
        return CarState(soc=result["soc"], range=range_km, soc_timestamp=result["soc_timestamp"],
                        odometer=result.get("odometer"), warning=warning)
