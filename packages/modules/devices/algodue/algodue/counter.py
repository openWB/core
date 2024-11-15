#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.devices.algodue.algodue.config import AlgodueCounterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store


class AlgodueCounter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, AlgodueCounterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(AlgodueCounterSetup, component_config)
        self.__tcp_client = tcp_client
        self.__modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.__tcp_client:

            frequency = self.__tcp_client.read_input_registers(0x1038, ModbusDataType.FLOAT_32, unit=self.id)
            currents = self.__tcp_client.read_input_registers(0x100E, [ModbusDataType.FLOAT_32]*3, unit=self.id)
            powers = self.__tcp_client.read_input_registers(0x1020, [ModbusDataType.FLOAT_32]*3, unit=self.id)
            power = sum(powers)
            voltages = self.__tcp_client.read_input_registers(0x1000, [ModbusDataType.FLOAT_32]*3, unit=self.id)

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            voltages=voltages,
            currents=currents,
            powers=powers,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AlgodueCounterSetup)
