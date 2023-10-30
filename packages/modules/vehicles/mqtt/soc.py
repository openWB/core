#!/usr/bin/env python3
import logging

from modules.vehicles.mqtt.config import MqttSocSetup
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: MqttSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        log.debug("MQTT-Fahrzeuge müssen nicht ausgelesen werden.")
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=MqttSocSetup)
