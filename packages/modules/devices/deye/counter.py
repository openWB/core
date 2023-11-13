#!/usr/bin/env python3
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
        unit = self.component_config.configuration.modbus_id
        currents = [c / 100 for c in client.read_holding_registers(613, [ModbusDataType.INT_16]*3, unit=unit)]
        voltages = client.read_holding_registers(644, [ModbusDataType.INT_16]*3, unit=unit)
        powers = client.read_holding_registers(616, [ModbusDataType.INT_16]*3, unit=unit)
        power = sum(powers)

        # Wenn der Import/export Netz in wh gerechnet wird => *100 !! kommt in kw/h *0.1
        imported = client.read_holding_registers(522, ModbusDataType.INT_16, unit=unit) * 100
        exported = client.read_holding_registers(524, ModbusDataType.INT_16, unit=unit) * 100

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeCounterSetup)
