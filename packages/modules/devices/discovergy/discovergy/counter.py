from requests import Session

from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.discovergy.discovergy import api
from modules.devices.discovergy.discovergy.config import DiscovergyCounterSetup
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentType


class DiscovergyCounter(AbstractCounter):
    def __init__(self, component_config: DiscovergyCounterSetup) -> None:
        self.component_config = component_config

    def initialize(self) -> None:
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self, session: Session):
        reading = api.get_last_reading(session, self.component_config.configuration.meter_id)

        imported, exported = self.peak_filter.check_values(reading.power, reading.imported, reading.exported)
        self.store.set(CounterState(
            imported=imported,
            exported=exported,
            power=reading.power,
            voltages=reading.voltages,
            powers=reading.powers
        ))


component_descriptor = ComponentDescriptor(configuration_factory=DiscovergyCounterSetup)
