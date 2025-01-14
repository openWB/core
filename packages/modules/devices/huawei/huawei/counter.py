#!/usr/bin/env python3
import time
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.huawei.huawei.config import HuaweiCounterSetup
from modules.devices.huawei.huawei.type import HuaweiType


class HuaweiCounter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, HuaweiCounterSetup],
                 modbus_id: int,
                 type: HuaweiType) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(HuaweiCounterSetup, component_config)
        self.modbus_id = modbus_id
        self.type = type
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_):
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        currents = client.read_holding_registers(37107, [ModbusDataType.INT_32]*3, unit=self.modbus_id)
        currents = [val / -100 for val in currents]
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        power = client.read_holding_registers(37113, ModbusDataType.INT_32, unit=self.modbus_id) * -1

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=HuaweiCounterSetup)
