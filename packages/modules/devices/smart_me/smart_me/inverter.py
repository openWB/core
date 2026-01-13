#!/usr/bin/env python3
import logging
from requests import Session

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.devices.smart_me.smart_me.config import SmartMeInverterSetup

log = logging.getLogger(__name__)


class SmartMeInverter(AbstractInverter):
    def __init__(self, component_config: SmartMeInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, session: Session) -> None:
        response = session.get('https://smart-me.com:443/api/Devices/' +
                               self.component_config.configuration.id, timeout=3).json()

        self.store.set(InverterState(
            exported=response["CounterReadingExport"] * 1000,
            power=response["ActivePower"] * 1000,
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SmartMeInverterSetup)
