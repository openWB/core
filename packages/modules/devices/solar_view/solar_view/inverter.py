#!/usr/bin/env python3
import logging

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.solar_view.solar_view.api import request
from modules.devices.solar_view.solar_view.config import SolarViewInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class SolarViewInverter(AbstractInverter):
    def __init__(self, component_config: SolarViewInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self, ip_address: str, port: int, timeout: int) -> None:
        values = request(ip_address, port, timeout, self.component_config.configuration.command)

        power = -1 * int(values[10])
        exported = 1000 * int(values[9])
        _, exported = self.peak_filter.check_values(power, None, exported)
        self.store.set(InverterState(
            exported=exported,
            power=power
        ))


component_descriptor = ComponentDescriptor(configuration_factory=SolarViewInverterSetup)
