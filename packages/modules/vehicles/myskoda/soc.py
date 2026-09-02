#!/usr/bin/env python3
import logging

from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.myskoda import api
from modules.vehicles.myskoda.config import Myskoda

log = logging.getLogger(__name__)


def fetch(vehicle_config: Myskoda, vehicle: int) -> CarState:
    config = vehicle_config.configuration

    data, key_expires_at = api.fetch_vehicle(config.api_key, config.vin)

    # Ablaufdatum nur bei Änderung zurückschreiben, um nicht bei jedem Zyklus
    # unnötig eine retained MQTT-Message zu publishen
    if key_expires_at and key_expires_at != config.key_expires_at:
        config.key_expires_at = key_expires_at
        Pub().pub(f"openWB/set/vehicle/{vehicle}/soc_module/config", asdict(vehicle_config))

    soc = api.extract_soc(data)
    range_km = api.extract_range(data)
    odometer_km = api.extract_odometer(data)

    return CarState(soc=soc, range=range_km, odometer=odometer_km)


def create_vehicle(vehicle_config: Myskoda, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_config, vehicle)

    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               # SoC ist während der Ladung über die Public API abrufbar,
                               # daher keine manuelle Berechnung nötig
                               calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=Myskoda)
