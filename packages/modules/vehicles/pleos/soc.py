#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.pleos import api
from modules.vehicles.pleos.config import Pleos

log = logging.getLogger(__name__)


def fetch(vehicle_config: Pleos, vehicle_update_data: VehicleUpdateData) -> CarState:
    config = vehicle_config.configuration
    if not config.vin:
        raise Exception("Pleos: VIN muss konfiguriert sein.")
    config.token = api.validate_token(config.brand, config.client_id, config.client_secret, config.token)
    battery = api.get_battery(config.brand, config.vin, config.token)
    charge = battery.get('charge', {})
    soc = float(charge['stateOfCharge'])
    soc_timestamp = api.parse_timestamp(battery.get('timestamp'))
    target_soc = charge.get('targetStateOfCharge', {}).get('standard')
    warning = (f"Das Fahrzeug begrenzt die Ladung selbst auf {target_soc}%."
               if target_soc and target_soc < 100 else None)
    range = api.get_distance_to_empty_km(config.brand, config.vin, config.token)
    odometer = api.get_odometer_km(config.brand, config.vin, config.token)
    return CarState(soc=soc, range=range, soc_timestamp=soc_timestamp, odometer=odometer, warning=warning)


def create_vehicle(vehicle_config: Pleos, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_config, vehicle_update_data)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=Pleos)
