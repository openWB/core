#!/usr/bin/env python3
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from requests import Session

from modules.devices.fronius.fronius_http_api.config import MeterLocation

log = logging.getLogger(__name__)

# Der Einbauort eines Zählers ändert sich zur Laufzeit nicht. Liefert die Fronius-API das
# Location-Feld einmal nicht (siehe Fronius-API-Eigenheiten), wird auf den zuletzt erfolgreich
# gelesenen Wert zurückgegriffen, statt die Komponente abstürzen zu lassen.
_last_known_location: Dict[str, MeterLocation] = {}


@dataclass
class FroniusMeterValues:
    location: MeterLocation
    powers: List[float]
    power_sum: float
    voltages: List[float]
    power_factors: List[float]
    frequency: float


def read_meter(session: Session,
               ip_address: str,
               meter_id: int,
               variant: int,
               cache_key: str,
               meter_system_response: Optional[Dict] = None) -> FroniusMeterValues:
    """Liest und normalisiert die Werte eines Fronius SmartMeters, unabhängig von der API-Variante."""
    if variant in (0, 1):
        data = _fetch_device_scope(session, ip_address, meter_id, variant)
        location_key = "Meter_Location_Current"
        power_sum_key = "PowerReal_P_Sum"
        powers = [data["PowerReal_P_Phase_"+str(num)] for num in range(1, 4)]
        voltages = [data["Voltage_AC_Phase_"+str(num)] for num in range(1, 4)]
        power_factors = [data["PowerFactor_Phase_"+str(num)] for num in range(1, 4)]
        frequency = data["Frequency_Phase_Average"]
    elif variant == 2:
        if meter_system_response is None:
            raise ValueError("meter_system_response wird für Variante 2 benötigt")
        data = dict(meter_system_response["Body"]["Data"]).get(str(meter_id))
        location_key = "SMARTMETER_VALUE_LOCATION_U16"
        power_sum_key = "SMARTMETER_POWERACTIVE_MEAN_SUM_F64"
        powers = [data["SMARTMETER_POWERACTIVE_MEAN_0"+str(num)+"_F64"] for num in range(1, 4)]
        voltages = [data["SMARTMETER_VOLTAGE_0"+str(num)+"_F64"] for num in range(1, 4)]
        power_factors = [data["SMARTMETER_FACTOR_POWER_0"+str(num)+"_F64"] for num in range(1, 4)]
        frequency = data["GRID_FREQUENCY_MEAN_F32"]
    else:
        raise ValueError("Unbekannte Variante: "+str(variant))

    location = _get_location(data, location_key, cache_key)

    return FroniusMeterValues(
        location=location,
        powers=powers,
        power_sum=data[power_sum_key],
        voltages=voltages,
        power_factors=power_factors,
        frequency=frequency
    )


def get_flow_power(powerflow_response) -> Tuple[float, float]:
    # Beim Energiebezug ist nicht klar, welcher Anteil aus dem Netz bezogen wurde, und was aus
    # dem Wechselrichter kam.
    # Beim Energieexport ist nicht klar, wie hoch der Eigenverbrauch während der Produktion war.
    if isinstance(powerflow_response, Exception):
        raise powerflow_response
    power_load = float(powerflow_response["Body"]["Data"]["Site"]["P_Grid"])
    power_inverter = float(powerflow_response["Body"]["Data"]["Site"]["P_PV"] or 0)
    return power_load, power_inverter


def _fetch_device_scope(session: Session, ip_address: str, meter_id: int, variant: int) -> Dict:
    if variant == 0:
        params = (('Scope', 'Device'), ('DeviceId', meter_id))
    else:
        params = (('Scope', 'Device'), ('DeviceId', meter_id), ('DataCollection', 'MeterRealtimeData'))
    response = session.get(
        'http://' + ip_address + '/solar_api/v1/GetMeterRealtimeData.cgi',
        params=params,
        timeout=5)
    return response.json()["Body"]["Data"]


def _get_location(data: Dict, location_key: str, cache_key: str) -> MeterLocation:
    try:
        location = MeterLocation.get(data[location_key])
    except KeyError:
        cached = _last_known_location.get(cache_key)
        if cached is None:
            raise
        log.warning(f"Feld '{location_key}' fehlt in der Fronius-Antwort, "
                    f"verwende zwischengespeicherten Einbauort {cached} (Zähler {cache_key})")
        return cached
    _last_known_location[cache_key] = location
    return location
