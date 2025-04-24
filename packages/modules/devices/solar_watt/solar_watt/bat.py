#!/usr/bin/env python3
import logging
from typing import Any, Dict, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solar_watt.solar_watt.api import parse_value
from modules.devices.solar_watt.solar_watt.config import SolarWattBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int


class SolarWattBat(AbstractBat):
    def __init__(self, component_config: SolarWattBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict, energy_manager: bool) -> None:
        if energy_manager:
            exported_temp = parse_value(response, "PowerConsumedFromStorage")
            imported_temp = parse_value(response, "PowerOutFromStorage")
            inside_temp = parse_value(response, "PowerBuffered")
            power = (exported_temp + imported_temp - inside_temp) * -1
            soc = parse_value(response, "StateOfCharge")
        else:
            power = response["FData"]["IBat"] * response["FData"]["VBat"] * -1
            soc = response["SData"]["SoC"]
        imported, exported = self.sim_counter.sim_count(power)
        self.store.set(BatState(
            imported=imported,
            exported=exported,
            power=power,
            soc=soc
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SolarWattBatSetup)
