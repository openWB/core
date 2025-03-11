from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.bmwbc import api
from modules.vehicles.bmwbc.config import BMWbc, BMWbcConfiguration


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: BMWbc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(
            vehicle_config.configuration.user_id,
            vehicle_config.configuration.password,
            vehicle_config.configuration.vin,
            vehicle_config.configuration.captcha_token,
            vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


def bmwbc_update(user_id: str, password: str, vin: str, captcha_token: str, charge_point: int):
    log.debug("bmwbc: user_id="+user_id+"vin="+vin+"charge_point="+str(charge_point))
    log.debug("bmwbc: captcha_token="+captcha_token)
    vehicle_config = BMWbc(configuration=BMWbcConfiguration(charge_point,
                                                            user_id,
                                                            password,
                                                            vin,
                                                            captcha_token))
    store.get_car_value_store(charge_point).store.set(api.fetch_soc(
        vehicle_config.configuration.user_id,
        vehicle_config.configuration.password,
        vehicle_config.configuration.vin,
        vehicle_config.configuration.captcha_token,
        charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(bmwbc_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=BMWbc)
