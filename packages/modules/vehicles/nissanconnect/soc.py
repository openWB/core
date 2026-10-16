from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.nissanconnect.api import NissanClient
from modules.vehicles.nissanconnect.config import NissanConnect


def create_vehicle(vehicle_config: NissanConnect, vehicle: int):
    client = None
    configuration_key = None

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        nonlocal client, configuration_key
        config = vehicle_config.configuration
        current = (config.user_id, config.password, config.vin)
        # Reuse tokens until credentials or vehicle selection change.
        if client is None or current != configuration_key:
            client = NissanClient(*current)
            configuration_key = current
        soc_percent, range_km, measurement_unix_seconds, odometer_km = client.fetch_battery()
        return CarState(soc=soc_percent, range=range_km, soc_timestamp=measurement_unix_seconds, odometer=odometer_km)

    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater,
                               vehicle=vehicle, calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=NissanConnect)
