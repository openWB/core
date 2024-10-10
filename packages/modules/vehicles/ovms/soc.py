from typing import List

import logging

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.ovms import api
from modules.vehicles.ovms.config import OVMS, OVMSConfiguration

log = logging.getLogger(__name__)


def fetch(vehicle_update_data: VehicleUpdateData, config: OVMS, vehicle: int) -> CarState:
    soc, range, soc_ts = api.fetch_soc(config, vehicle)
    return CarState(soc, range)


def create_vehicle(vehicle_config: OVMS, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_update_data, vehicle_config, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


def ovms_update(server_url: str, user_id: str, password: str, vehicleId: str, token: str, charge_point: int):
    log.debug("ovms: server_url=" + server_url +
              "user_id=" + user_id +
              "vehicleId=" + vehicleId +
              "charge_point=" + str(charge_point))
    store.get_car_value_store(charge_point).store.set(
        fetch(None,
              OVMS(configuration=OVMSConfiguration(server_url, user_id, password, vehicleId, token)), charge_point))


def main(argv: List[str]):
    run_using_positional_cli_args(ovms_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=OVMS)
