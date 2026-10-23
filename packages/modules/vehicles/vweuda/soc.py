from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.vweuda.config import VWEUDA
from modules.vehicles.vweuda.libeuda import EudaVehicle


def create_vehicle(vehicle_config: VWEUDA, vehicle: int) -> ConfigurableVehicle[VWEUDA]:
    portal = EudaVehicle(vehicle_config.configuration, vehicle)

    # Functions are shared by deepcopy: both callbacks keep the same portal cache.
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return portal.fetch(vehicle_update_data)

    return ConfigurableVehicle(
        vehicle_config=vehicle_config,
        component_updater=updater,
        vehicle=vehicle,
        calc_while_charging=vehicle_config.configuration.calculate_soc,
        request_interval_override=lambda: portal.get_request_interval_override(),
    )


device_descriptor = DeviceDescriptor(configuration_factory=VWEUDA)
