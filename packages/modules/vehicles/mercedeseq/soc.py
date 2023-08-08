import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import SocUpdateData
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.common.component_state import CarState

from modules.vehicles.mercedeseq.config import MercedesEQSoc
import modules.vehicles.mercedeseq.api as api


log = logging.getLogger("soc."+__name__)


def fetch(vehicle_config: MercedesEQSoc, soc_update_data: SocUpdateData, vehicle) -> CarState:
    soc, range = api.fetch_soc(vehicle_config, vehicle)
    return CarState(soc, range)


def create_vehicle(vehicle_config: MercedesEQSoc, vehicle: int):
    def updater(soc_update_data: SocUpdateData) -> CarState:
        return fetch(vehicle_config, soc_update_data, vehicle)
    return ConfigurableVehicle(vehicle_config=vehicle_config, component_updater=updater, vehicle=vehicle)


device_descriptor = DeviceDescriptor(configuration_factory=MercedesEQSoc)
