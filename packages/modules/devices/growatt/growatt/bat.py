#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.growatt.growatt.config import GrowattBatSetup
from modules.devices.growatt.growatt.version import GrowattVersion


class GrowattBat(AbstractBat):
    def __init__(self,
                 component_config: Union[Dict, GrowattBatSetup],
                 modbus_id: int,
                 version: GrowattVersion) -> None:
        self.__modbus_id = modbus_id
        self.version = version
        self.component_config = dataclass_from_dict(GrowattBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        if self.version == GrowattVersion.max_series:
            power_in = client.read_input_registers(
                1011, ModbusDataType.UINT_32, unit=self.__modbus_id) * -0.1
            power_out = client.read_input_registers(
                1009, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.1
            power = power_in + power_out

            soc = client.read_input_registers(1014, ModbusDataType.UINT_16, unit=self.__modbus_id)
            imported = client.read_input_registers(
                1058, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            exported = client.read_input_registers(
                1054, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            power_in = client.read_input_registers(
                3180, ModbusDataType.UINT_32, unit=self.__modbus_id) * -0.1
            power_out = client.read_input_registers(
                3178, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.1
            power = power_in + power_out

            soc = client.read_input_registers(3171, ModbusDataType.UINT_16, unit=self.__modbus_id)
            imported = client.read_input_registers(
                3131, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            exported = client.read_input_registers(
                3127, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattBatSetup)
