#!/usr/bin/env python3
import logging
from typing import Dict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.solar_log.solar_log.config import SolarLogInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class SolarLogInverter(AbstractInverter):
    def __init__(self,
                 component_config: SolarLogInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self, response: Dict) -> None:
        self.store.set(self.get_values(response))

    def get_values(self, response: Dict) -> InverterState:
        power = -abs(float(response["801"]["170"]["101"]))
        exported = float(response["801"]["170"]["109"])
        _, exported = self.peak_filter.check_values(power, None, exported)
        return InverterState(
            exported=exported,
            power=power
        )


component_descriptor = ComponentDescriptor(configuration_factory=SolarLogInverterSetup)
