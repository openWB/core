#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.ampere.ampere.config import AmpereCounterSetup


class AmpereCounter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, AmpereCounterSetup],
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(AmpereCounterSetup, component_config)
        self.modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_):
        powers = client.read_input_registers(1349, [ModbusDataType.INT_16]*3, unit=self.modbus_id)
        power = client.read_input_registers(1348, ModbusDataType.INT_16, unit=self.modbus_id)

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=powers,
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AmpereCounterSetup)
