import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.byd import api
from modules.vehicles.byd.config import Byd

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: Byd, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return api.fetch_soc(vehicle_config.configuration, vehicle)

    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               # SoC während der Ladung über die Cloud-API abrufbar,
                               # daher keine manuelle Berechnung nötig
                               calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=Byd)
