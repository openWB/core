import logging
import jq

from typing import List, Optional, Union, Any, Dict
from datetime import datetime

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.json.config import JsonSocSetup, JsonSocConfiguration


log = logging.getLogger(__name__)


def extract_to_epoch(input_string: Union[str, int, float]) -> float:
    # If already an integer, return it
    if isinstance(input_string, int) or isinstance(input_string, float):
        return int(input_string)

    # Try parsing as UTC formatted time
    try:
        dt = datetime.fromisoformat(input_string)
        return int(dt.timestamp())
    except ValueError:
        log.exception(f'Kein ISO 8601 formatiertes Datum in "{input_string}" gefunden.')
        return None


def parse_data(data: Dict[str, Any], compiled_query: Any, pattern: str = None) -> any:
    if compiled_query is None:
        raise ValueError("Kein Pattern zum extrahieren der Daten definiert. Bitte die Konfiguration aktualisieren!")

    result = compiled_query.input(data).first()
    if result is None:
        raise ValueError(f'Pattern "{pattern}" hat keine Ergebnisse in "{data}" geliefert!')

    log.debug(f'result="{result}"')
    return result


def fetch_soc(config: JsonSocSetup, compiled_queries: Dict) -> CarState:
    url = config.configuration.url
    timeout = config.configuration.timeout if isinstance(config.configuration.timeout, int) else None

    if url is None or url == "":
        raise ValueError("Keine URL zum Abrufen der Daten definiert. Bitte in der Konfiguration aktualisieren.")
    if compiled_queries["soc"] is None:
        raise ValueError("Kein Pattern zum Extrahieren des SOC definiert. Bitte in der Konfiguration aktualisieren.")

    raw_data: Dict[str, Any] = req.get_http_session().get(url, timeout=timeout).json()

    soc = float(parse_data(raw_data, compiled_queries["soc"], config.configuration.soc_pattern))
    range = (int(parse_data(raw_data, compiled_queries["range"], config.configuration.range_pattern))
             if compiled_queries["range"] is not None else None)
    timestamp = (extract_to_epoch(parse_data(raw_data,
                                             compiled_queries["timestamp"],
                                             config.configuration.timestamp_pattern))
                 if compiled_queries["timestamp"] is not None else None)
    return CarState(soc=soc, range=range, soc_timestamp=timestamp)


def initialize_vehicle(vehicle_config: JsonSocSetup, compiled_queries: Dict) -> None:
    config = vehicle_config.configuration
    log.debug(f'Initialisiere Fahrzeug mit Konfiguration: {config}')
    compiled_queries["soc"] = jq.compile(config.soc_pattern) if config.soc_pattern is not None else None
    compiled_queries["range"] = jq.compile(config.range_pattern) if config.range_pattern is not None else None
    compiled_queries["timestamp"] = (jq.compile(config.timestamp_pattern)
                                     if config.timestamp_pattern is not None else None)


def create_vehicle(vehicle_config: JsonSocSetup, vehicle: int):
    compiled_queries = {
        'soc': None,
        'range': None,
        'timestamp': None
    }

    def initializer() -> None:
        return initialize_vehicle(vehicle_config, compiled_queries)

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config, compiled_queries)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc,
                               initializer=initializer)


def json_update(charge_point: int,
                url: str,
                soc_pattern: str,
                range_pattern: Optional[str] = None,
                timestamp_pattern: Optional[str] = None,
                calculate_soc: Optional[bool] = False):
    log.debug(f'json-soc: charge_point={charge_point} url="{url}" soc-pattern="{soc_pattern}" '
              f'range-pattern="{range_pattern}" timestamp-pattern="{timestamp_pattern}" calculate-soc={calculate_soc}')
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(JsonSocSetup(configuration=JsonSocConfiguration(url=url,
                                                                  soc_pattern=soc_pattern,
                                                                  range_pattern=range_pattern,
                                                                  timestamp_pattern=timestamp_pattern,
                                                                  calculate_soc=calculate_soc))))


def main(argv: List[str]):
    run_using_positional_cli_args(json_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=JsonSocSetup)
