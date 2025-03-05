#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.upower.upower.config import UPowerBatSetup
from modules.devices.upower.upower.version import UPowerVersion


class UPowerBat(AbstractBat):
    def __init__(self,
                 component_config: Union[Dict, UPowerBatSetup],
                 version: UPowerVersion,
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(UPowerBatSetup, component_config)
        self.__modbus_id = modbus_id
        self.version = version
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")

    def update(self, client: ModbusTcpClient_) -> None:
        if self.version == UPowerVersion.GEN_1:
            power = client.read_input_registers(30258, ModbusDataType.INT_32, unit=self.__modbus_id) * -1
            soc = client.read_input_registers(33000, ModbusDataType.UINT_16, unit=self.__modbus_id)
            imported = client.read_input_registers(
                31108, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            exported = client.read_input_registers(
                31110, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            # 1221 Total Bat Power
            # 1427 Battery 1 current power
            # Bat 1 (additional batteries offset by 50)
            power = client.read_input_registers(1427, ModbusDataType.INT_16, unit=self.__modbus_id)
            soc = client.read_input_registers(1402, ModbusDataType.UINT_16, unit=self.__modbus_id) / 10
            imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=UPowerBatSetup)
