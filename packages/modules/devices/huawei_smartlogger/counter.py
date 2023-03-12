#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.huawei_smartlogger.config import Huawei_SmartloggerCounterSetup


class Huawei_SmartloggerCounter:
    def __init__(self,device_id: int, 
                 component_config: Huawei_SmartloggerCounterSetup, 
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(Huawei_SmartloggerCounterSetup, component_config)
        self.client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self):
        modbus_id = self.component_config.configuration.modbus_id
        power = self.client.read_holding_registers(32278, ModbusDataType.INT_32, unit=modbus_id)
        currents = [val / 100 for val in self.client.read_holding_registers(32272, [ModbusDataType.INT_32] * 3, unit=modbus_id)]
        voltages = [val / 100 for val in self.client.read_holding_registers(32260, [ModbusDataType.INT_32] * 3, unit=modbus_id)]
        powers = [val / 1000 for val in self.client.read_holding_registers(32335, [ModbusDataType.INT_32] * 3, unit=modbus_id)]
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=Huawei_SmartloggerCounterSetup)
