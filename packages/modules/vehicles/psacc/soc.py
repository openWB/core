#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.vehicles.psacc.config import PSACCVehicleSoc
from modules.vehicles.json.soc import create_vehicle

__all__ = ['create_vehicle', 'device_descriptor']  # declare as exported

device_descriptor = DeviceDescriptor(configuration_factory=PSACCVehicleSoc)
