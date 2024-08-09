#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.azzurro_zcs.azzurro_zcs.config import ZCSCounterSetup


class ZCSCounter:
    def __init__(self,
                 component_config: Union[Dict, ZCSCounterSetup],
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(ZCSCounterSetup, component_config)
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_):
        # 0x0212 Grid Power Int16 -10-10 kW Unit 0,01kW Feed in/out power
        # 0x0214 Input/Output power Int16 -10-10kW 0,01kW Energy storage power inverter
        power = client.read_input_registers(0x0212, ModbusDataType.INT_16, wordorder=Endian.Little,
                                            unit=self.__modbus_id) * -1
        # 0x020C Grid frequency UInt 0-100 Hz Unit 0,01 Hz
        frequency = client.read_input_registers(
            0x020C, ModbusDataType.UINT_16, unit=self.__modbus_id) / 100
        try:
            # 0x0206 A phase voltage UInt 0-1000V unit 0,1V
            # 0x0207 A phase current Int 0-100A Unit 0,01A, rms
            # 0x0230 R-Phase voltage UInt Unit 0,1V
            # 0x0231 R-Phase current UInt Unit 0,01A
            powers = (client.read_input_registers(
                0x0206, ModbusDataType.UINT_16, unit=self.__modbus_id) / 10) * \
                (client.read_input_registers(0x0207, ModbusDataType.INT_16, unit=self.__modbus_id) / 10)
        except Exception:
            powers = None

        exported = [value * 10
                    for value in client.read_input_registers(
                        # 0x021E Total energy injected into the grid UInt16 Unit 1kWh high
                        # 0x021F Total energy injected into the grid UInt16 Unit 1kWh low
                        0x021E, [ModbusDataType.UINT_16] * 10,
                        wordorder=Endian.Little, unit=self.__modbus_id)]
        imported = [value * 10
                    for value in client.read_input_registers(
                        # 0x0220 Total energy taken from the grid UInt16 Unit 1kWh high
                        # 0x0221 Total energy taken from the grid UInt16 Unit 1kWh low
                        0x0220, [ModbusDataType.UINT_16] * 10,
                        wordorder=Endian.Little, unit=self.__modbus_id)]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ZCSCounterSetup)
