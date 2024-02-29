from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.renault import api
from modules.vehicles.renault.config import Renault, RenaultConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: Renault, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(vehicle_config.configuration)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def renault_update(user_id: str, password: str, location: str, country: str, vin: str, charge_point: int):
    log.debug("renault: user_id=" + user_id + "vin=" + vin + "charge_point=" + str(charge_point))
    store.get_car_value_store(charge_point).store.set(api.fetch_soc(
        RenaultConfiguration(charge_point, user_id, password, location, country, vin)))


def main(argv: List[str]):
    run_using_positional_cli_args(renault_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Renault)
