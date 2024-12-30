#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.vehicles.psacc.config import PSACCVehicleSoc
from modules.vehicles.json.soc import create_vehicle as create_vehicle_json

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: PSACCVehicleSoc, vehicle: int):
    return create_vehicle_json(vehicle_config, vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=PSACCVehicleSoc)
