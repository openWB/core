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


log = logging.getLogger(__name__)


def fetch_soc(config: JsonSocSetup) -> CarState:
    soc_url = config.configuration.soc_url
    soc_pattern = config.configuration.soc_pattern
    range_url = config.configuration.range_url
    range_pattern = config.configuration.range_pattern

    if soc_url is None or soc_url == "none":
        log.warning("http_soc: soc_url not defined - set soc to 0")
        soc = 0
    else:
        raw_soc = req.get_http_session().get(soc_url, timeout=5).json()
        soc = float(jq.compile(soc_pattern).input(raw_soc).first())
    if range_url is None or range_url == "none":
        log.warning("http_soc: range_url not defined - set range to null")
        range = 0
    else:
        raw_range = req.get_http_session().get(range_url, timeout=5).json()
        range = int(jq.compile(range_pattern).input(raw_range).first())
    return CarState(soc, range)


def create_vehicle(vehicle_config: JsonSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def http_update(soc_url: str, range_url: str, charge_point: int):
    log.debug("http_soc: soc_url="+soc_url+"range_url="+range_url+"charge_point="+str(charge_point))
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(JsonSocSetup(configuration=JsonSocConfiguration(soc_url, range_url))))


def main(argv: List[str]):
    run_using_positional_cli_args(http_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=JsonSocSetup)
