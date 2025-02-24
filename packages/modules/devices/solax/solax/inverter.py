#!/usr/bin/env python3
from typing import Any, TypedDict
from pymodbus.constants import Endian

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store
from modules.devices.solax.solax.config import SolaxInverterSetup, Solax
from modules.devices.solax.solax.version import SolaxVersion


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    device_config: Solax


class SolaxInverter(AbstractInverter):
    def __init__(self, component_config: SolaxInverterSetup, **kwargs: Any) -> None:
        self.component_config = SolaxInverterSetup(**component_config)
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client = self.kwargs['client']
        self.device_config = self.kwargs['device_config']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.device_config.configuration.modbus_id

        if SolaxVersion(self.device_config.configuration.version) == SolaxVersion.G2:
            power = self.__tcp_client.read_input_registers(0x0413, ModbusDataType.UINT_16, unit=unit) * -1
            exported = self.__tcp_client.read_input_registers(
                0x0423, ModbusDataType.UINT_32, wordorder=Endian.Little, unit=unit) * 100
        elif SolaxVersion(self.device_config.configuration.version) == SolaxVersion.G3:
            power_temp = self.__tcp_client.read_input_registers(0x000A, [ModbusDataType.UINT_16] * 2, unit=unit)
            power = sum(power_temp) * -1
            exported = self.__tcp_client.read_input_registers(
                0x0052, ModbusDataType.UINT_32, wordorder=Endian.Little, unit=unit) * 100
        else:
            power_temp = self.__tcp_client.read_input_registers(0x0410, [ModbusDataType.UINT_16] * 2, unit=unit)
            power = sum(power_temp) * -1
            exported = self.__tcp_client.read_input_registers(
                0x042B, ModbusDataType.UINT_32, wordorder=Endian.Little, unit=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolaxInverterSetup)
