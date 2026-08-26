from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.enecess.ecomain import config
from modules.devices.enecess.ecomain.config import EcoMainInverterSetup
from modules.devices.enecess.ecomain.runtime import EcoMainRuntime


SOURCE_TOKENS = {0: "h", 1: "s1", 2: "s2", 3: "s3"}


class EcoMainInverter(AbstractInverter):
    def __init__(
            self,
            component_config: EcoMainInverterSetup,
            runtime: EcoMainRuntime,
            device_id: int) -> None:
        self.component_config = component_config
        self.runtime = runtime
        self.device_id = device_id

    def initialize(self) -> None:
        self.channels = config.validate_inverter_configuration(
            self.component_config.configuration
        )
        self.store = get_component_value_store(
            self.component_config.type,
            self.component_config.id,
        )
        self.fault_state = FaultState(
            ComponentInfo.from_component_config(self.component_config)
        )
        self.peak_filter = PeakFilter(
            ComponentType.INVERTER,
            self.component_config.id,
            self.fault_state,
        )
        self.runtime.ensure_compatible()

    def read_state(self) -> InverterState:
        configuration = self.component_config.configuration
        factor = 1 if configuration.invert else -1
        powers = []
        currents = [0.0, 0.0, 0.0]
        exported = 0.0
        imported = 0.0
        for channel in self.channels:
            reading = self.runtime.read_channel(channel.source, channel.channel)
            corrected_power = reading.power * factor
            powers.append(corrected_power)
            currents[channel.phase - 1] = (
                -abs(reading.current) if corrected_power < 0 else abs(reading.current)
            )
            if configuration.invert:
                exported += reading.reverse_energy
                imported += reading.forward_energy
            else:
                exported += reading.forward_energy
                imported += reading.reverse_energy
        power = sum(powers)
        imported, exported = self.peak_filter.check_values(power, imported, exported)
        serial_channels = "_".join(
            f"l{channel.phase}-{SOURCE_TOKENS[channel.source]}-c{channel.channel:02d}"
            for channel in self.channels
        )
        return InverterState(
            power=power,
            currents=currents,
            exported=exported,
            imported=imported,
            serial_number=f"{self.runtime.device_serial}_inv_{serial_channels}",
        )

    def update(self) -> None:
        self.store.set(self.read_state())


component_descriptor = ComponentDescriptor(configuration_factory=EcoMainInverterSetup)
