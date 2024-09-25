#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.mtec.mtec.config import MTecCounterSetup


class MTecCounter:
    def __init__(self, device_id: int, component_config: MTecCounterSetup) -> None:
        self.component_config = dataclass_from_dict(MTecCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__device_id = device_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")

    def update(self, client: ModbusTcpClient_):
        unit = self.component_config.configuration.modbus_id

        power = client.read_holding_registers(11000, ModbusDataType.INT_32, unit=unit)
        powers = client.read_holding_registers(10994, [ModbusDataType.INT_32]*3, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=MTecCounterSetup)
