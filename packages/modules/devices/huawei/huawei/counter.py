#!/usr/bin/env python3
import time
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.huawei.huawei.config import HuaweiCounterSetup
from modules.devices.huawei.huawei.type import HuaweiType


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    type: HuaweiType
    client: ModbusTcpClient_


class HuaweiCounter(AbstractCounter):
    def __init__(self, component_config: HuaweiCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.type: HuaweiType = self.kwargs['type']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        currents = self.client.read_holding_registers(37107, [ModbusDataType.INT_32]*3, unit=self.modbus_id)
        currents = [val / -100 for val in currents]
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        power = self.client.read_holding_registers(37113, ModbusDataType.INT_32, unit=self.modbus_id) * -1

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=HuaweiCounterSetup)
