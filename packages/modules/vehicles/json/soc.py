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


log = logging.getLogger(__name__)


def parse_data(data: Dict[str, Any], pattern: str) -> float:
    log.debug(f"parse_data: data='{data}' pattern='{pattern}'")

    if pattern == "":
        raise ValueError("Please provide pattern to parse data")

    result = jq.compile(pattern).input(data).first()
    if result is None:
        raise ValueError(f"Pattern {pattern} did not match any data in {data}")

    return float(result)


def fetch_soc(config: JsonSocSetup) -> CarState:
    url = config.configuration.url
    soc_pattern = config.configuration.soc_pattern
    range_pattern = config.configuration.range_pattern
    timeout = config.configuration.timeout if isinstance(config.configuration.timeout, int) else None

    if url is None or url == "":
        log.warning("url not defined, set soc to 0")
        return CarState(0, 0)
    else:
        raw_data: Dict[str, Any] = req.get_http_session().get(url, timeout=timeout).json()

    soc = parse_data(raw_data, soc_pattern)

    if range_pattern is None or range_pattern == "":
        log.warning("range_pattern not defined, set range to 0")
        range = 0
    else:
        range = int(parse_data(raw_data, range_pattern))

    return CarState(soc, range)


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
