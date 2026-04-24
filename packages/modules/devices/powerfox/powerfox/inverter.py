#!/usr/bin/env python3
import logging
from requests import Session

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.powerfox.powerfox.config import PowerfoxInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class PowerfoxInverter(AbstractInverter):
    def __init__(self, component_config: PowerfoxInverterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self, session: Session) -> None:
        response = session.get('https://backend.powerfox.energy/api/2.0/my/' + self.component_config.configuration.id +
                               '/current', timeout=3).json()

        _, exported = self.peak_filter.check_values(float(response['Watt']),
                                                    None,
                                                    float(response['A_Plus']))

        self.store.set(InverterState(
            exported=exported,
            power=float(response['Watt'])
        ))


component_descriptor = ComponentDescriptor(configuration_factory=PowerfoxInverterSetup)
