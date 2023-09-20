from typing import List

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.evnotify import api
from modules.vehicles.evnotify.config import EVNotify, EVNotifyConfiguration


def create_vehicle(vehicle_config: EVNotify, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return CarState(soc=api.fetch_soc(
            vehicle_config.configuration.akey, vehicle_config.configuration.token))
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def evnotify_update(akey: str, token: str, charge_point: int):
    vehicle_config = EVNotify(configuration=EVNotifyConfiguration(charge_point, akey, token))
    store.get_car_value_store(charge_point).store.set(
        CarState(soc=api.fetch_soc(
            vehicle_config.configuration.akey, vehicle_config.configuration.token)))


def main(argv: List[str]):
    run_using_positional_cli_args(evnotify_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=EVNotify)
