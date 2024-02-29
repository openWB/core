from typing import List
import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.http.config import HttpSocSetup, HttpSocConfiguration


log = logging.getLogger(__name__)


def fetch_soc(config: HttpSocSetup) -> CarState:
    soc_url = config.configuration.soc_url
    range_url = config.configuration.range_url
    if soc_url is None or soc_url == "none":
        log.warn("http_soc: soc_url not defined - set soc to 0")
        soc = 0
    else:
        soc_text = req.get_http_session().get(soc_url, timeout=5).text
        soc = int(soc_text)
    if range_url is None or range_url == "none":
        log.warn("http_soc: range_url not defined - set range to 0.0")
        range = float(0)
    else:
        range_text = req.get_http_session().get(range_url, timeout=5).text
        range = float(range_text)
    return CarState(soc, range)


def create_vehicle(vehicle_config: HttpSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def http_update(soc_url: str, range_url: str, charge_point: int):
    log.debug("http_soc: soc_url="+soc_url+"range_url="+range_url+"charge_point="+str(charge_point))
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(HttpSocSetup(configuration=HttpSocConfiguration(soc_url, range_url))))


def main(argv: List[str]):
    run_using_positional_cli_args(http_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=HttpSocSetup)
