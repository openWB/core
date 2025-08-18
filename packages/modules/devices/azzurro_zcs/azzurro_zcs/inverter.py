#!/usr/bin/env python3
from typing import TypedDict, Any
from pymodbus.constants import Endian

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.azzurro_zcs.azzurro_zcs.config import ZCSInverterSetup


class KwargsDict(TypedDict):
    modbus_id: int
    client: ModbusTcpClient_


class ZCSInverter(AbstractInverter):
    def __init__(self, component_config: ZCSInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        # 0x0252 PV1 Power UInt16 0-100kW Unit 0,01kW
        # 0x0250 PV1 Voltage UInt16 0-1000V Unit 0,1V
        # 0x0251 PV1 current Int16 0-100A Unit 0,01A
        power_string1 = (self.client.read_input_registers(
            0x0250, ModbusDataType.UINT_16, unit=self.__modbus_id) / 10) * \
            (self.client.read_input_registers(0x0251, ModbusDataType.INT_16, unit=self.__modbus_id) / 10)
        # 0x0255 PV2 Power UInt16 0-100 kW Unit 0,01kW
        # 0x0253 PV2 Voltage UInt16 0-1000V Unit 0,1V
        # 0x0254 PV2 current Int16 0-100A Unit 0,01A
        power_string2 = (self.client.read_input_registers(
            0x0253, ModbusDataType.INT_16, unit=self.__modbus_id) / 10) * \
            (self.client.read_input_registers(0x0254, ModbusDataType.INT_16, unit=self.__modbus_id) / 10)
        power = (power_string1 + power_string2) * -1
        # 0x0215 PV Power generation UInt16 0 -10 kW Unit 0,01kW
        exported = self.client.read_input_registers(0x0215, ModbusDataType.UINT_16, wordorder=Endian.Little,
                                                    unit=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ZCSInverterSetup)
