#!/usr/bin/env python3
import time
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.deye.config import DeyeCounterSetup


class DeyeCounter:
    def __init__(self, component_config: DeyeCounterSetup) -> None:
        self.component_config = dataclass_from_dict(DeyeCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: ModbusTcpClient_):
        unit = 1
        power = client.read_holding_registers(40618, ModbusDataType.INT_32, unit=unit)
        time.sleep(0.05)
        currents = [c * 100 for c in client.read_holding_registers(40614, [ModbusDataType.INT_32]*3, unit=unit)]
        time.sleep(0.05)
        powers = client.read_holding_registers(40617, [ModbusDataType.INT_32]*3, unit=unit)
        time.sleep(0.05)
        imported = client.read_holding_registers(40522, ModbusDataType.INT_32, unit=unit) * 100
        time.sleep(0.05)
        exported = client.read_holding_registers(40524, ModbusDataType.INT_32, unit=unit) * 100
        time.sleep(0.05)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeCounterSetup)
