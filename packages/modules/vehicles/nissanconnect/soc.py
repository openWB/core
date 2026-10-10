"""Adapt Nissan measurements to the existing openWB vehicle wrapper and scheduler."""
import json
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.nissanconnect.src.api import NissanClient, RequestCounter
from modules.vehicles.nissanconnect.config import NissanConnect


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: NissanConnect, vehicle: int):
    """Keep one client per configuration; delegate scheduling/error policy to Core."""
    client = None
    configuration_key = None
    # Per configured vehicle, including client replacement after edited credentials.
    # Restart/recreation discards history; no file, MQTT topic or Core state is added.
    request_counter = RequestCounter()

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        nonlocal client, configuration_key
        config = vehicle_config.configuration
        current = (config.user_id, config.password, config.vin)
        # Keep tokens between updates; discard them when the account/vehicle changes.
        if client is None or current != configuration_key:
            client = NissanClient(*current, request_counter=request_counter)
            configuration_key = current
        try:
            battery = client.fetch_battery(include_odometer=True)
        finally:
            # No account identifiers or secrets; battery values/times are still private.
            if isinstance(client.last_query, dict):
                log.debug("Nissan vehicle %s query: %s", vehicle, json.dumps(client.last_query, sort_keys=True))
        return CarState(soc=battery.soc_percent, range=battery.range_km, soc_timestamp=battery.measurement_unix_seconds,
                        odometer=battery.odometer_km)

    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater,
                               vehicle=vehicle, calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=NissanConnect)
