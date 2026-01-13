#!/usr/bin/env python3
import logging

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.devices.solar_view.solar_view.api import request
from modules.devices.solar_view.solar_view.config import SolarViewInverterSetup

log = logging.getLogger(__name__)


class SolarViewInverter(AbstractInverter):
    def __init__(self, component_config: SolarViewInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, ip_address: str, port: int, timeout: int) -> None:
        values = request(ip_address, port, timeout, self.component_config.configuration.command)
        self.store.set(InverterState(
            exported=1000 * int(values[9]),
            power=-1 * int(values[10])
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SolarViewInverterSetup)
