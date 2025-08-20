#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.marstek.marstek.config import MarstekBatSetup  # Adjust path if needed


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_
    modbus_id: int


class MarstekBat(AbstractBat):
    def __init__(self, component_config: MarstekBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        modbus_id = self.__modbus_id

        power = self.__tcp_client.read_holding_registers(32202,
                                                         ModbusDataType.INT_32, unit=modbus_id) * -1
        soc = self.__tcp_client.read_holding_registers(32104,
                                                       ModbusDataType.UINT_16, unit=modbus_id) * 0.1
        imported = self.__tcp_client.read_holding_registers(33000,
                                                            ModbusDataType.UINT_32, unit=modbus_id) * 0.01
        exported = self.__tcp_client.read_holding_registers(33002,
                                                            ModbusDataType.UINT_32, unit=modbus_id) * 0.01

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported_scaled,
            exported=exported_scaled
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=MarstekBatSetup)
