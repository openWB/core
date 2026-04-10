import logging
import time
from typing import List, Optional

from requests.exceptions import RequestException

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.bmw_cardata.config import BmwCardataSetup, BmwCardataConfiguration

log = logging.getLogger(__name__)

BMW_AUTH_URL = "https://customer.bmwgroup.com/gcdm/oauth"
BMW_API_URL = "https://api-cardata.bmwgroup.com"

FIELD_SOC = "vehicle.drivetrain.electricEngine.charging.level"
FIELD_SOC_ALT = "vehicle.drivetrain.batteryManagement.header"
FIELD_RANGE = "vehicle.drivetrain.electricEngine.remainingElectricRange"
FIELD_STATUS = "vehicle.drivetrain.electricEngine.charging.status"
FIELD_ODOMETER_CANDIDATES = [
    "vehicle.vehicle.travelledDistance",
    "vehicle.trip.segment.end.travelledDistance",
]

CONTAINER_NAME = "ChargeStats"
CONTAINER_PURPOSE = "openWB"
CONTAINER_DESCRIPTORS = [
    "vehicle.drivetrain.electricEngine.charging.status",
    "vehicle.drivetrain.electricEngine.charging.level",
    "vehicle.drivetrain.batteryManagement.header",
    "vehicle.drivetrain.electricEngine.remainingElectricRange",
    "vehicle.vehicle.travelledDistance",
]


def _get_session(token: Optional[str] = None):
    session = req.get_http_session()
    session.headers.update({
        "Accept": "application/json",
        "x-version": "v1",
    })
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def _response_text(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc)
    try:
        return response.text or str(exc)
    except Exception:
        return str(exc)


def _extract_http_status(exc: Exception) -> Optional[int]:
    response = getattr(exc, "response", None)
    if response is not None:
        return getattr(response, "status_code", None)
    return None


def _extract_value(td: dict, key: str):
    entry = td.get(key, {})
    return entry.get("value") if isinstance(entry, dict) else None


def _extract_first_value(td: dict, keys: List[str]):
    for key in keys:
        value = _extract_value(td, key)
        if value is not None:
            return value
    return None


def _post_form(url: str, data: dict) -> dict:
    session = _get_session()
    response = session.post(url, data=data)
    return response.json()


def _get_json(url: str, token: str):
    session = _get_session(token)
    response = session.get(url)
    return response.json()


def _post_json(url: str, token: str, payload: dict) -> dict:
    session = _get_session(token)
    response = session.post(url, json=payload)
    return response.json()


def _create_container(token: str) -> str:
    log.warning("BMW CarData: Keine aktiven Container gefunden. Erstelle neuen Container...")
    result = _post_json(
        f"{BMW_API_URL}/customers/containers",
        token,
        {
            "name": CONTAINER_NAME,
            "purpose": CONTAINER_PURPOSE,
            "technicalDescriptors": CONTAINER_DESCRIPTORS,
        },
    )
    container_id = result.get("containerId") or result.get("id")
    if not container_id:
        raise Exception(f"BMW CarData: Container konnte nicht erstellt werden: {result}")
    log.info("BMW CarData: Container erstellt: %s", container_id)
    return container_id


def _fetch_telematic_data(token: str, vin: str, container_id: str):
    url = f"{BMW_API_URL}/customers/vehicles/{vin}/telematicData?containerId={container_id}"
    log.debug("BMW CarData: GET %s", url)
    return _get_json(url, token)


def get_valid_token(cfg: BmwCardataConfiguration) -> str:
    if not cfg.access_token:
        raise Exception("BMW CarData: Keine Tokens gefunden. Bitte BMW-Kopplung in der UI durchführen.")

    if time.time() < cfg.expires_at:
        return cfg.access_token

    log.info("BMW CarData: Token abgelaufen, führe Refresh durch...")
    try:
        new = _post_form(
            f"{BMW_AUTH_URL}/token",
            {
                "grant_type": "refresh_token",
                "refresh_token": cfg.refresh_token,
                "client_id": cfg.client_id,
            },
        )
    except RequestException as e:
        raise Exception(
            f"BMW CarData: Token-Refresh fehlgeschlagen: {e}. Bitte BMW-Kopplung erneut durchführen."
        )

    cfg.access_token = new["access_token"]
    cfg.refresh_token = new.get("refresh_token", cfg.refresh_token)
    cfg.expires_at = time.time() + new.get("expires_in", 3600) - 60

    log.info("BMW CarData: Token-Refresh erfolgreich.")
    return cfg.access_token


def get_container_id(cfg: BmwCardataConfiguration, token: str) -> str:
    if cfg.container_id:
        log.debug("BMW CarData: Container-ID aus Konfiguration: %s", cfg.container_id)
        return cfg.container_id

    log.info("BMW CarData: Ermittle Container-ID via API...")
    raw = _get_json(f"{BMW_API_URL}/customers/containers", token)
    containers = raw if isinstance(raw, list) else raw.get("containers", [])

    openwb = [
        c for c in containers
        if c.get("state") == "ACTIVE" and c.get("purpose") == CONTAINER_PURPOSE
    ]
    active = [c for c in containers if c.get("state") == "ACTIVE"]
    preferred = openwb if openwb else active

    if preferred:
        container_id = preferred[0].get("containerId") or preferred[0].get("id")
        log.info("BMW CarData: Container-ID gefunden: %s", container_id)
    else:
        container_id = _create_container(token)

    cfg.container_id = container_id
    return container_id


def fetch_soc(config: BmwCardataSetup) -> CarState:
    cfg = config.configuration

    if not cfg.client_id:
        raise Exception("BMW CarData: client_id nicht konfiguriert!")
    if not cfg.vin:
        raise Exception("BMW CarData: VIN nicht konfiguriert!")

    token = get_valid_token(cfg)
    container_id = get_container_id(cfg, token)

    try:
        raw = _fetch_telematic_data(token, cfg.vin, container_id)
    except RequestException as e:
        status_code = _extract_http_status(e)

        if status_code in (400, 404):
            log.warning(
                "BMW CarData: Container %s ungültig (HTTP %s), ermittle neu...",
                container_id,
                status_code,
            )
            cfg.container_id = ""
            container_id = get_container_id(cfg, token)
            raw = _fetch_telematic_data(token, cfg.vin, container_id)
        else:
            if status_code == 403 and "CU-429" in _response_text(e):
                raise Exception("BMW CarData: Tageslimit erreicht (CU-429).")
            raise Exception(f"BMW CarData: API-Fehler beim Abruf der Telematikdaten: {e}")

    td = raw.get("telematicData", raw)

    soc_raw = _extract_value(td, FIELD_SOC)
    if soc_raw is None:
        soc_raw = _extract_value(td, FIELD_SOC_ALT)

    range_raw = _extract_value(td, FIELD_RANGE)
    status = _extract_value(td, FIELD_STATUS)
    odometer_raw = _extract_first_value(td, FIELD_ODOMETER_CANDIDATES)

    soc = int(float(soc_raw)) if soc_raw is not None else None
    vehicle_range = int(float(range_raw)) if range_raw is not None else None
    odometer = int(float(odometer_raw)) if odometer_raw is not None else None

    if soc is None:
        raise Exception("BMW CarData: Kein SoC-Wert in API-Antwort gefunden!")

    log.info(
        "BMW CarData: SoC=%s%%, Reichweite=%s km, Status=%s, Odometer=%s km",
        soc,
        vehicle_range,
        status,
        odometer,
    )
    return CarState(soc=soc, range=vehicle_range, odometer=odometer)


def create_vehicle(vehicle_config: BmwCardataSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)

    return ConfigurableVehicle(
        vehicle_config=vehicle_config,
        component_updater=updater,
        vehicle=vehicle,
        calc_while_charging=vehicle_config.configuration.calculate_soc,
    )


device_descriptor = DeviceDescriptor(configuration_factory=BmwCardataSetup)
