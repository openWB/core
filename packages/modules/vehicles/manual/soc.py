#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.manual.calc_soc import calc_soc
from modules.vehicles.manual.config import ManualSoc

log = logging.getLogger(__name__)


def fetch(vehicle_config: ManualSoc, soc_update_data: SocUpdateData):
    soc = calc_soc(soc_update_data,
                   vehicle_config.configuration.efficiency,
                   vehicle_config.configuration.soc_start,
                   soc_update_data.battery_capacity)
    return CarState(soc)


def create_vehicle(vehicle_config: ManualSoc, vehicle: int):
    def updater(soc_update_data: SocUpdateData) -> CarState:
        return fetch(vehicle_config, soc_update_data)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=ManualSoc)
