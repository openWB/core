#!/usr/bin/env python3
import logging

from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc, SocUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo
from modules.vehicles.manual.calc_soc import calc_soc
from modules.vehicles.manual.config import ManualSoc

log = logging.getLogger(__name__)


class Soc(AbstractSoc):
    def __init__(self, soc_config: ManualSoc, vehicle: int):
        self.soc_config = soc_config
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.soc_config.name, "vehicle")

    def update(self, soc_update_data: SocUpdateData) -> None:
        with SingleComponentUpdateContext(self.component_info):
            soc = calc_soc(soc_update_data,
                           self.soc_config.configuration.efficiency,
                           self.soc_config.configuration.soc_start,
                           soc_update_data.battery_capacity)
            self.store.set(CarState(soc))


device_descriptor = DeviceDescriptor(configuration_factory=ManualSoc)
