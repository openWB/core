#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.manual.config import ManualSoc


def create_vehicle(vehicle_config: ManualSoc, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        pass
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=ManualSoc)
