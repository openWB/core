from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.psa import api
from modules.vehicles.psa.config import PSA, PSAConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: PSA, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(vehicle_config.configuration, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=True)


def psa_update(user_id: str,
               password: str,
               client_id: str,
               client_secret: str,
               manufacturer: str,
               calculate_soc: bool,
               vin: str,
               charge_point: int):
    log.debug("psa-update: user_id=%s, VIN=%s, chargepoint=%s", user_id, vin, charge_point)
    store.get_car_value_store(charge_point).store.set(api.fetch_soc(PSAConfiguration(
        user_id=user_id,
        password=password,
        client_id=client_id,
        client_secret=client_secret,
        manufacturer=manufacturer,
        calculate_soc=calculate_soc,
        vin=vin), charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(psa_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=PSA)
