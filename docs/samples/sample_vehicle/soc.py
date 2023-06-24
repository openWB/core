#!/usr/bin/env python3
import logging

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.sample_vehicle.config import SampleVehicleSoc

log = logging.getLogger(__name__)


def fetch(vehicle_config: SampleVehicleSoc, soc_update_data: SocUpdateData) -> CarState:
    response = req.get_http_session().get(vehicle_config.configuration.ip_address, timeout=5).json()
    # Soc und -falls vorhanden- Reichweite aus Antwort parsen
    return CarState(soc, range)


def create_vehicle(vehicle_config: SampleVehicleSoc, vehicle: int):
    def updater(soc_update_data: SocUpdateData) -> CarState:
        return fetch(vehicle_config, soc_update_data)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=SampleVehicleSoc)
