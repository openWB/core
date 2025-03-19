#!/usr/bin/env python3
import time
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.huawei.huawei.config import HuaweiInverterSetup
from modules.devices.huawei.huawei.type import HuaweiType


class HuaweiInverter(AbstractInverter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, HuaweiInverterSetup],
                 modbus_id: int,
                 type: HuaweiType) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(HuaweiInverterSetup, component_config)
        self.modbus_id = modbus_id
        self.type = type
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        if self.type == HuaweiType.SDongle:
            time.sleep(1)
        power = client.read_holding_registers(32064, ModbusDataType.INT_32, unit=self.modbus_id) * -1

        _, exported = self.sim_counter.sim_count(power)
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=HuaweiInverterSetup)
