#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.good_we.good_we.config import GoodWeBatSetup
from modules.devices.good_we.good_we.version import GoodWeVersion


class KwargsDict(TypedDict):
    modbus_id: int
    version: GoodWeVersion
    firmware: int
    client: modbus.ModbusTcpClient_


class GoodWeBat(AbstractBat):
    def __init__(self, component_config: GoodWeBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GoodWeVersion = self.kwargs['version']
        self.firmware: int = self.kwargs['firmware']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)
        with self.__tcp_client:
            if battery_index == 1:
                if self.version == GoodWeVersion.V_1_7:
                    power = self.__tcp_client.read_holding_registers(
                        35183, ModbusDataType.INT_16, unit=self.__modbus_id)*-1
                else:
                    power = self.__tcp_client.read_holding_registers(
                        35182, ModbusDataType.INT_32, unit=self.__modbus_id)*-1
                soc = self.__tcp_client.read_holding_registers(37007, ModbusDataType.UINT_16, unit=self.__modbus_id)
                imported = self.__tcp_client.read_holding_registers(
                    35206, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
                exported = self.__tcp_client.read_holding_registers(
                    35209, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            else:
                power = self.__tcp_client.read_holding_registers(35182, ModbusDataType.INT_32, unit=self.__modbus_id)*-1
                soc = self.__tcp_client.read_holding_registers(37007, ModbusDataType.UINT_16, unit=self.__modbus_id)
                imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=GoodWeBatSetup)
