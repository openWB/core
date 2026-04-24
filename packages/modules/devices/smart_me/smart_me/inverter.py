#!/usr/bin/env python3
import logging
from requests import Session

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.smart_me.smart_me.config import SmartMeInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class SmartMeInverter(AbstractInverter):
    def __init__(self, component_config: SmartMeInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self, session: Session) -> None:
        response = session.get('https://smart-me.com:443/api/Devices/' +
                               self.component_config.configuration.id, timeout=3).json()

        exported = response["CounterReadingExport"] * 1000
        power = response["ActivePower"] * 1000
        _, exported = self.peak_filter.check_values(power, None, exported)
        self.store.set(InverterState(
            exported=exported,
            power=power,
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SmartMeInverterSetup)
