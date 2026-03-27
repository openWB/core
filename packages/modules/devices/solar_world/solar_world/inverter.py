#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.solar_world.solar_world.config import SolarWorldInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int


class SolarWorldInverter(AbstractInverter):
    def __init__(self, component_config: SolarWorldInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self, response) -> None:
        try:
            power = response["PowerTotalPV"] * -1
        except ValueError:
            # wenn eManager aus bzw. keine Antwort ersetze leeren Wert durch eine 0
            power = 0
        self.peak_filter.check_values(power)
        exported = self.sim_counter.sim_count(power)[1]

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolarWorldInverterSetup)
