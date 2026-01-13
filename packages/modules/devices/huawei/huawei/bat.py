#!/usr/bin/env python3
import time
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.huawei.huawei.config import HuaweiBatSetup
from modules.devices.huawei.huawei.type import HuaweiType


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    type: HuaweiType
    client: ModbusTcpClient_


class HuaweiBat(AbstractBat):
    def __init__(self, component_config: HuaweiBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.type: HuaweiType = self.kwargs['type']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        power = self.client.read_holding_registers(37765, ModbusDataType.INT_32, unit=self.modbus_id)
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        soc = self.client.read_holding_registers(37760, ModbusDataType.INT_16, unit=self.modbus_id) / 10

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=HuaweiBatSetup)
