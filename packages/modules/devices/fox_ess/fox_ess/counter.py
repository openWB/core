#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.fox_ess.fox_ess.config import FoxEssCounterSetup


class FoxEssCounter:
    def __init__(self, component_config: FoxEssCounterSetup) -> None:
        self.component_config = dataclass_from_dict(FoxEssCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_):
        unit = self.component_config.configuration.modbus_id

        powers = client.read_holding_registers(31026, [ModbusDataType.INT_16]*3, unit=unit)
        power = sum(powers)
        frequency = client.read_holding_registers(31015, ModbusDataType.UINT_16, unit=unit) / 100
        imported = client.read_holding_registers(32018, ModbusDataType.UINT_32, unit=unit) * 100
        exported = client.read_holding_registers(32015, ModbusDataType.UINT_32, unit=unit) * 100

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssCounterSetup)
