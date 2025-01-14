from typing import List
import logging
import jq

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.json.config import JsonSocSetup, JsonSocConfiguration
from typing import Any, Dict
from datetime import datetime


log = logging.getLogger(__name__)


def extract_to_epoch(input_string: str) -> float:
    # If already an integer, return it
    if isinstance(input_string, int) or isinstance(input_string, float):
        return int(input_string)

    # Try parsing as UTC formatted time
    try:
        dt = datetime.fromisoformat(input_string)
        return int(dt.timestamp())
    except ValueError:
        log.exception(f"Kein ISO 8601 formatiertes Datum in '{input_string}' gefunden.")
        return None


def parse_data(data: Dict[str, Any], pattern: str) -> any:
    log.debug(f"parse_data: data='{data}' pattern='{pattern}'")

    if pattern == "":
        raise ValueError("Kein Pattern zum extrahieren der Daten definiert. Bitte in der Konfiguration aktualisieren.")

    result = jq.compile(pattern).input(data).first()
    if result is None:
        raise ValueError(f"Pattern {pattern} hat keine Ergebnisse in '{data}' geliefert.")

    log.debug(f"result='{result}'")
    return result


def fetch_soc(config: JsonSocSetup) -> CarState:
    url = config.configuration.url
    soc_pattern = config.configuration.soc_pattern
    range_pattern = config.configuration.range_pattern
    timestamp_pattern = config.configuration.timestamp_pattern
    timeout = config.configuration.timeout if isinstance(config.configuration.timeout, int) else None

    if url is None or url == "":
        raise ValueError("Keine URL zum Abrufen der Daten definiert. Bitte in der Konfiguration aktualisieren.")

    raw_data: Dict[str, Any] = req.get_http_session().get(url, timeout=timeout).json()

    soc = float(parse_data(raw_data, soc_pattern))

    if range_pattern is None or range_pattern == "":
        log.debug("Kein Pattern für Range angegeben, setze Range auf None.")
        range = None
    else:
        range = int(parse_data(raw_data, range_pattern))

    if timestamp_pattern is None or timestamp_pattern == "":
        log.debug("Kein Pattern für Timestamp angegeben, setze Timestamp auf None.")
        timestamp = None
    else:
        log.debug(f"timestamp_pattern='{timestamp_pattern}'")
        timestamp = parse_data(raw_data, timestamp_pattern)
        timestamp = extract_to_epoch(timestamp)

    return CarState(soc=soc, range=range, soc_timestamp=timestamp)


def create_vehicle(vehicle_config: JsonSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


def http_update(soc_url: str, range_url: str, charge_point: int):
    log.debug("http_soc: soc_url="+soc_url+"range_url="+range_url+"charge_point="+str(charge_point))
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(JsonSocSetup(configuration=JsonSocConfiguration(soc_url, range_url))))


def main(argv: List[str]):
    run_using_positional_cli_args(http_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=JsonSocSetup)
