from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.bmw import api
from modules.vehicles.bmw.config import BMW, BMWConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: BMW, vehicle: int):
    def updater(soc_update_data: SocUpdateData) -> CarState:
        return api.fetch_soc(
            vehicle_config.configuration.user_id,
            vehicle_config.configuration.password,
            vehicle_config.configuration.vin,
            vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def bmw_update(user_id: str, password: str, vin: str, charge_point: int):
    log.debug("bmw: user_id="+user_id+"vin="+vin+"charge_point="+str(charge_point))
    vehicle_config = BMW(configuration=BMWConfiguration(charge_point, user_id, password, vin))
    store.get_car_value_store(charge_point).store.set(api.fetch_soc(
        vehicle_config.configuration.user_id,
        vehicle_config.configuration.password,
        vehicle_config.configuration.vin,
        charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(bmw_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=BMW)
