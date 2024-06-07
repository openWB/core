import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.smarthello import api
from modules.vehicles.smarthello.config import SmartHello


log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: SmartHello, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(vehicle_config.configuration, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=SmartHello)
