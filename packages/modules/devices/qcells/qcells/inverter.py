#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.qcells.qcells.config import QCellsInverterSetup


class QCellsInverter:
    def __init__(self,
                 component_config: Union[Dict, QCellsInverterSetup],
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(QCellsInverterSetup, component_config)
        self.__modbus_id = modbus_id
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        power_string1 = (client.read_input_registers(
            0x0003, ModbusDataType.INT_16, unit=self.__modbus_id) / 10) * \
            (client.read_input_registers(0x0005, ModbusDataType.INT_16, unit=self.__modbus_id) / 10)
        power_string2 = (client.read_input_registers(
            0x0004, ModbusDataType.INT_16, unit=self.__modbus_id) / 10) * \
            (client.read_input_registers(0x0006, ModbusDataType.INT_16, unit=self.__modbus_id) / 10)
        power = (power_string1 + power_string2) * -1
        exported = client.read_input_registers(0x0094, ModbusDataType.UINT_32, wordorder=Endian.Little,
                                               unit=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=QCellsInverterSetup)
