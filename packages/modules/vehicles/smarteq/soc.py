from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.smarteq import api
from modules.vehicles.smarteq.config import SmartEQ, SmartEQConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: SmartEQ, vehicle: int):
    def updater(soc_update_data: SocUpdateData) -> CarState:
        return api.fetch_soc(vehicle_config, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)

# def smarteq_update(user_id: str, password: str, vin: str, refreshToken: str, charge_point: int):


def smarteq_update(user_id: str, password: str, vin: str, charge_point: int):
    log.debug("smarteq: userid="+user_id+"vin="+vin+"charge_point="+str(charge_point))
    store.get_car_value_store(charge_point).store.set(
        api.fetch_soc(SmartEQ(configuration=SmartEQConfiguration(user_id, password, vin)), charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(smarteq_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=SmartEQ)
