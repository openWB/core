import logging
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.deye.deye_solarman.config import DeyeSolarmanBatSetup
from modules.devices.deye.deye_solarman.device_type import DeviceType
from modules.common.component_type import ComponentType
from pysolarmanv5 import PySolarmanV5 as ModbusSolarmanClient_

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusSolarmanClient_


class DeyeSolarmanBat(AbstractBat):
    def __init__(self, component_config: DeyeSolarmanBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusSolarmanClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.device_type = DeviceType(self.client.read_holding_registers(0, 1)[0])

    def update(self) -> None:
        if self.device_type == DeviceType.SINGLE_PHASE_STRING or self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
            power = self.client.read_holding_registers(190, 1)[0] * -1
            soc = self.client.read_holding_registers(184, 1)[0]

            if self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
                imported = self.client.read_holding_registers(72, 1)[0] * 100
                exported = self.client.read_holding_registers(74, 1)[0] * 100
                imported, exported = self.peak_filter.check_values(power, imported, exported)

            elif self.device_type == DeviceType.SINGLE_PHASE_STRING:
                self.peak_filter.check_values(power)
                imported, exported = self.sim_counter.sim_count(power)

        else:  # THREE_PHASE_LV (0x0500, 0x0005), THREE_PHASE_HV (0x0006)
            power = self.client.read_holding_registers(590, 1)[0] * -1

            if self.device_type == DeviceType.THREE_PHASE_HV:
                power = power * 10
            soc = self.client.read_holding_registers(588, 1)[0]
            self.peak_filter.check_values(power)
            imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeSolarmanBatSetup)
