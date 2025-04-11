#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.azzurro_zcs.azzurro_zcs.config import ZCSBatSetup


class KwargsDict(TypedDict):
    modbus_id: int
    client: ModbusTcpClient_


class ZCSBat(AbstractBat):
    def __init__(self, component_config: ZCSBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        # 0x020D Battery charge-discharge power Int16 -10-10 kW accuracy 0,01 kW pos charge, neg discharge
        # 0x020E Battery voltage Cell UInt16 0-100 V accuracy 0,1 V
        # 0x020F Battery charge-discharge current Int -100-100 A accuracy 0,01A
        power = self.client.read_input_registers(0x020D, ModbusDataType.INT_16, unit=self.__modbus_id)
        # 0x0210 SoC UInt16 0-100 %
        soc = self.client.read_input_registers(0x0210, ModbusDataType.UINT_16, unit=self.__modbus_id)
        # 0x0227 Total energy charging battery low UInt16 in kWh LSB
        imported = self.client.read_input_registers(
            0x0227, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
        # 0x0229 Total energy discharging battery low UInt16 in kWh LSB
        exported = self.client.read_input_registers(
            0x0229, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=ZCSBatSetup)
