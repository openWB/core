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

            frequency = self.__tcp_client.read_input_registers(0x1038, ModbusDataType.FLOAT_32, unit=self.__modbus_id)
            currents = self.__tcp_client.read_input_registers(
                0x100E, [ModbusDataType.FLOAT_32]*3, unit=self.__modbus_id)
            powers = self.__tcp_client.read_input_registers(0x1020, [ModbusDataType.FLOAT_32]*3, unit=self.__modbus_id)
            power = sum(powers)
            voltages = self.__tcp_client.read_input_registers(
                0x1000, [ModbusDataType.FLOAT_32]*3, unit=self.__modbus_id)

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

# serial_chars = self.client.read_holding_registers(0x500, [ModbusDataType.UINT_8]*10, unit=self.id)
# model_id = self.client.read_holding_registers(0x505, ModbusDataType.UINT_16, unit=self.id)
# model_string = "unknown"
# if model_id == 0x03:
#     model_string = "6 A, 3 phases, 4 wires"
# elif model_id == 0x08:
#     model_string = "80 A, 3 phases, 4 wires"
# elif model_id == 0x0c:
#     model_string = "80 A, 1 phase, 2 wires"
# elif model_id == 0x10:
#     model_string = "40 A, 1 phase, 2 wires"
# elif model_id == 0x12:
#     model_string = "63 A, 3 phases, 4 wires"

# type_id = self.client.read_holding_registers(0x506, ModbusDataType.UINT_16, unit=self.id)
# type_string = "unknown"
# if type_id == 0x00:
#     type_string = "NO MID, RESET"
# elif type_id == 0x01:
#     type_string = "MID"
# elif type_id == 0x02:
#     type_string = "NO MID"
# elif type_id == 0x03:
#     type_string = "NO MID, Wiring selection"
# elif type_id == 0x05:
#     type_string = "MID no varh"
# elif type_id == 0x09:
#     type_string = "MID Wiring selection"
# elif type_id == 0x0a:
#     type_string = "MID no varh, Wiring selection"
# elif type_id == 0x0b:
#     type_string = "NO MID, RESET, Wiring selection"
# meterinfo = "Algodue UEM " + model_string + ", " + type_string
