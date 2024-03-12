#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.evcc.config import EVCCVehicleSoc
from modules.vehicles.evcc.api import fetch_soc

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: EVCCVehicleSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config.configuration, vehicle_update_data, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


device_descriptor = DeviceDescriptor(configuration_factory=EVCCVehicleSoc)
