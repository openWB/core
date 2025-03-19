#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_, ModbusDataType
from modules.common.store import get_bat_value_store
from modules.devices.sma.sma_sunny_boy.config import SmaSunnyBoyBatSetup


class SunnyBoyBat(AbstractBat):
    SMA_UINT_64_NAN = 0xFFFFFFFFFFFFFFFF  # SMA uses this value to represent NaN

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SmaSunnyBoyBatSetup],
                 tcp_client: ModbusTcpClient_) -> None:
        self.component_config = dataclass_from_dict(SmaSunnyBoyBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def read(self) -> BatState:
        unit = self.component_config.configuration.modbus_id

        soc = self.__tcp_client.read_holding_registers(30845, ModbusDataType.UINT_32, unit=unit)
        imp = self.__tcp_client.read_holding_registers(31393, ModbusDataType.INT_32, unit=unit)
        exp = self.__tcp_client.read_holding_registers(31395, ModbusDataType.INT_32, unit=unit)
        if imp > 5:
            power = imp
        else:
            power = exp * -1

        exported = self.__tcp_client.read_holding_registers(31401, ModbusDataType.UINT_64, unit=unit)
        imported = self.__tcp_client.read_holding_registers(31397, ModbusDataType.UINT_64, unit=unit)

        if exported == self.SMA_UINT_64_NAN or imported == self.SMA_UINT_64_NAN:
            raise ValueError(f'Batterie lieferte nicht plausible Werte. Export: {exported}, Import: {imported}. ',
                             'Sobald die Batterie geladen/entladen wird sollte sich dieser Wert ändern, ',
                             'andernfalls kann ein Defekt vorliegen.')

        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def update(self) -> None:
        self.store.set(self.read())


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyBoyBatSetup)
