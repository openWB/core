from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.leaf import api
from modules.vehicles.leaf.config import LeafSoc, LeafConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: LeafSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(
            vehicle_config.configuration.user_id,
            vehicle_config.configuration.password,
            vehicle_config.configuration.region,
            vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle)
#                               calc_while_charging=False)


def leaf_update(user_id: str, password: str, region: str, vehicle: int):
    log.debug("Leaf: user_id="+user_id+" region="+region+" vehicle="+str(vehicle))
    vehicle_config = LeafSoc(configuration=LeafConfiguration(vehicle, user_id, password, region))
    store.get_car_value_store(vehicle).store.set(api.fetch_soc(
        vehicle_config.configuration.user_id,
        vehicle_config.configuration.password,
        vehicle_config.configuration.region,
        vehicle))


def main(argv: List[str]):
    run_using_positional_cli_args(leaf_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=LeafSoc)
