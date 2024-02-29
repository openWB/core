from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.kia import api
from modules.vehicles.kia.config import KIA, KIAConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: KIA, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(
            vehicle_config.configuration.user_id,
            vehicle_config.configuration.password,
            vehicle_config.configuration.pin,
            vehicle_config.configuration.vin,
            vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def kia_update(user_id: str, password: str, pin: str, vin: str, charge_point: int):
    vehicle_config = KIA(configuration=KIAConfiguration(charge_point, user_id, password, pin, vin))
    store.get_car_value_store(charge_point).store.set(api.fetch_soc(
        vehicle_config.configuration.user_id,
        vehicle_config.configuration.password,
        vehicle_config.configuration.pin,
        vehicle_config.configuration.vin,
        charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(kia_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=KIA)
