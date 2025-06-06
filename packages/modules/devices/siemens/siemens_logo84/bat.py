#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_bat_value_store
from modules.devices.siemens.siemens_logo84.config import SiemensLogo84BatSetup


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    modbus_id: int


class SiemensLogo84Bat(AbstractBat):
    def __init__(self, component_config: SiemensLogo84BatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        with self.__tcp_client:
            power = self.__tcp_client.read_holding_registers(342, ModbusDataType.INT_16, unit=self.__modbus_id) * -1
            soc = self.__tcp_client.read_holding_registers(343, ModbusDataType.INT_16, unit=self.__modbus_id)
            imported = self.__tcp_client.read_holding_registers(344, ModbusDataType.INT_16, unit=self.__modbus_id)*1000
            exported = self.__tcp_client.read_holding_registers(345, ModbusDataType.INT_16, unit=self.__modbus_id)*1000

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SiemensLogo84BatSetup)
