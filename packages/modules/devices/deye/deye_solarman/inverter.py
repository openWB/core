#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.utils.peak_filter import PeakFilter
from modules.common.store import get_inverter_value_store
from modules.devices.deye.deye_solarman.config import DeyeSolarmanInverterSetup
from modules.devices.deye.deye_solarman.device_type import DeviceType
from modules.common.component_type import ComponentType
from pysolarmanv5 import PySolarmanV5 as ModbusSolarmanClient_


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusSolarmanClient_


class DeyeSolarmanInverter(AbstractInverter):
    def __init__(self, component_config: DeyeSolarmanInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusSolarmanClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.device_type = DeviceType(self.client.read_holding_registers(0, 1)[0])

    def update(self) -> None:
        if self.device_type == DeviceType.SINGLE_PHASE_STRING or self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
            power = sum(self.client.read_holding_registers(186, 4)) * -1

        else:  # THREE_PHASE_LV (0x0500, 0x0005), THREE_PHASE_HV (0x0006)
            power = sum(self.client.read_holding_registers(672, 2)) * -1

            if self.device_type == DeviceType.THREE_PHASE_HV:
                power = power * 10
        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            imported=imported,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeSolarmanInverterSetup)
