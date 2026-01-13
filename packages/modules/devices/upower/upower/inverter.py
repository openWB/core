#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.upower.upower.config import UPowerInverterSetup
from modules.devices.upower.upower.version import UPowerVersion


class UPowerInverter(AbstractInverter):
    def __init__(self,
                 component_config: Union[Dict, UPowerInverterSetup],
                 version: UPowerVersion,
                 modbus_id: int,
                 client: ModbusTcpClient_) -> None:
        self.component_config = dataclass_from_dict(UPowerInverterSetup, component_config)
        self.__modbus_id = modbus_id
        self.version = version
        self.client = client
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        if self.version == UPowerVersion.GEN_1:
            power = self.client.read_holding_registers(11028, ModbusDataType.UINT_32, unit=self.__modbus_id) * -1
            exported = self.client.read_holding_registers(11020, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        else:
            power = self.client.read_holding_registers(1220, ModbusDataType.UINT_16, unit=self.__modbus_id) * -1
            exported = self.client.read_holding_registers(1006, ModbusDataType.UINT_32, unit=self.__modbus_id) * 10

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=UPowerInverterSetup)
