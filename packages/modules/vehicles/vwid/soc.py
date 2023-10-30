from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.vwid import api
from modules.vehicles.vwid.config import VWId, VWIdConfiguration


log = logging.getLogger(__name__)


def fetch(vehicle_update_data: VehicleUpdateData, config: VWId, vehicle: int) -> CarState:
    soc, range, soc_ts = api.fetch_soc(config, vehicle)
    log.info("Result: soc=" + str(soc)+", range=" + str(range) + "@" + soc_ts)
    return CarState(soc, range)


def create_vehicle(vehicle_config: VWId, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_update_data, vehicle_config, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def vwid_update(user_id: str, password: str, vin: str, refreshToken: str, charge_point: int):
    log.debug("vwid: user_id="+user_id+"vin="+vin+"charge_point="+str(charge_point))
    store.get_car_value_store(charge_point).store.set(
        fetch(None, VWId(configuration=VWIdConfiguration(user_id, password, vin, refreshToken)), charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(vwid_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=VWId)
