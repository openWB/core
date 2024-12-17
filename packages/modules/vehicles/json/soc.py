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


def fetch_data(url, timeout=5):
    if url is None or url == "none":
        return None
    raw_data = req.get_http_session().get(url, timeout=timeout).json()
    return raw_data


def parse_data(data, pattern):
    if pattern is None:
        return data
    return jq.compile(pattern).input(data).first()


def fetch_soc(config: JsonSocSetup) -> CarState:
    soc_url = config.configuration.soc_url
    soc_pattern = config.configuration.soc_pattern
    range_url = config.configuration.range_url
    range_pattern = config.configuration.range_pattern
    timeout = config.configuration.timeout if isinstance(config.configuration.timeout, int) else None

    soc_data = fetch_data(soc_url, timeout)
    if soc_data is None:
        log.warning("soc_url not defined, set soc to 0")
        soc = 0
    else:
        soc = float(parse_data(soc_data, soc_pattern))

    if range_url is None or range_url == "none" or range_url == "":
        log.warning("range_url not defined, set range to null")
        range = 0
    else:
        if range_url == soc_url:  # avoid duplicate http requests if range_url is the same as soc_url
            log.debug('range_url "{}" is same as soc_url "{}", reusing existing data.'.format(range_url, soc_url))
            range_data = soc_data
        else:
            range_data = fetch_data(range_url, timeout)
        range = int(parse_data(range_data, range_pattern))

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
