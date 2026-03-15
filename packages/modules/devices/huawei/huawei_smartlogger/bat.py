#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.huawei.huawei_smartlogger.config import Huawei_SmartloggerBatSetup


class KwargsDict(TypedDict):
    device_id: int
    tcp_client: modbus.ModbusTcpClient_


class Huawei_SmartloggerBat(AbstractBat):
    def __init__(self, component_config: Huawei_SmartloggerBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        power = self.__tcp_client.read_holding_registers(37765, ModbusDataType.INT_32, unit=modbus_id)
        soc = self.__tcp_client.read_holding_registers(37760, ModbusDataType.INT_16, unit=modbus_id) / 10

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=Huawei_SmartloggerBatSetup)
