#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.tronity.config import TronityVehicleSoc
from modules.vehicles.tronity.api import fetch_soc

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: TronityVehicleSoc, vehicle: int):
    def updater(soc_update_data: SocUpdateData) -> CarState:
        return fetch_soc(vehicle_config.configuration, soc_update_data, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=TronityVehicleSoc)
