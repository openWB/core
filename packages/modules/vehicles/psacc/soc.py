#!/usr/bin/env python3
import logging


from modules.common import req
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.psacc.config import PSACCVehicleSoc


log = logging.getLogger(__name__)


def fetch(vehicle_config: PSACCVehicleSoc, vehicle_update_data: VehicleUpdateData) -> CarState:
    c = vehicle_config.configuration
    url = f'http://{c.psacc_server_or_ip}:{c.psacc_port}/get_vehicleinfo/{c.vehicle_vin}'
    response = req.get_http_session().get(url, timeout=5).json()
    energy = response['energy'][0]
    return CarState(soc=energy['level'], range=energy['autonomy'])


def create_vehicle(vehicle_config: PSACCVehicleSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_config, vehicle_update_data)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=True)
