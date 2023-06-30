from typing import TypeVar, Generic, Callable

from modules.common import store
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo

T_VEHICLE_CONFIG = TypeVar("T_VEHICLE_CONFIG")


class IntervalConfig:
    def __init__(self,
                 request_interval_charging: int = 5,
                 request_interval_not_charging: int = 720,
                 request_only_plugged: bool = False) -> None:
        self.request_interval_charging = request_interval_charging
        self.request_interval_not_charging = request_interval_not_charging
        self.request_only_plugged = request_only_plugged


class ConfigurableVehicle(Generic[T_VEHICLE_CONFIG]):
    def __init__(self,
                 vehicle_config: T_VEHICLE_CONFIG,
                 component_updater: Callable[[T_VEHICLE_CONFIG, SocUpdateData], CarState],
                 vehicle: int,
                 interval_config: IntervalConfig = IntervalConfig()) -> None:
        self.__component_updater = component_updater
        self.vehicle_config = vehicle_config
        self.interval_config = interval_config
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.vehicle_config.name, "vehicle")

    def update(self, soc_update_data: SocUpdateData):
        with SingleComponentUpdateContext(self.component_info):
            self.store.set(self.__component_updater(soc_update_data))
