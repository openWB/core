#!/usr/bin/env python3
import logging
from requests import Session

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.powerfox.powerfox.config import PowerfoxCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class PowerfoxCounter(AbstractCounter):
    def __init__(self, component_config: PowerfoxCounterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self, session: Session) -> None:
        response = session.get('https://backend.powerfox.energy/api/2.0/my/' + self.component_config.configuration.id +
                               '/current', timeout=3).json()
        imported, exported = self.peak_filter.check_values(float(response['Watt']),
                                                           float(response['A_Plus']),
                                                           float(response['A_Minus']))
        self.store.set(CounterState(
            imported=imported,
            exported=exported,
            power=float(response['Watt'])
        ))


component_descriptor = ComponentDescriptor(configuration_factory=PowerfoxCounterSetup)
