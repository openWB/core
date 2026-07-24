from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.enecess.ecomain.config import EcoMainCounterSetup
from modules.devices.enecess.ecomain.runtime import EcoMainRuntime


class EcoMainCounter(AbstractCounter):
    def __init__(
            self,
            component_config: EcoMainCounterSetup,
            runtime: EcoMainRuntime,
            device_id: int) -> None:
        self.component_config = component_config
        self.runtime = runtime
        self.device_id = device_id

    def initialize(self) -> None:
        self.store = get_component_value_store(
            self.component_config.type,
            self.component_config.id,
        )
        self.fault_state = FaultState(
            ComponentInfo.from_component_config(self.component_config)
        )
        self.peak_filter = PeakFilter(
            ComponentType.COUNTER,
            self.component_config.id,
            self.fault_state,
        )
        self.runtime.ensure_compatible()

    def read_state(self) -> CounterState:
        reading = self.runtime.read_counter()
        imported, exported = self.peak_filter.check_values(
            reading.power,
            reading.imported,
            reading.exported,
        )
        return CounterState(
            power=reading.power,
            powers=reading.powers,
            voltages=reading.voltages,
            currents=reading.currents,
            power_factors=reading.power_factors,
            imported=imported,
            exported=exported,
            frequency=50,
            serial_number=f"{self.runtime.device_serial}_evu",
        )

    def update(self) -> None:
        self.store.set(self.read_state())


component_descriptor = ComponentDescriptor(configuration_factory=EcoMainCounterSetup)
