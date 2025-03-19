#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_, ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sma.sma_sunny_boy.config import SmaSunnyBoySmartEnergyBatSetup


class SunnyBoySmartEnergyBat(AbstractBat):
    SMA_UINT32_NAN = 0xFFFFFFFF  # SMA uses this value to represent NaN
    SMA_UINT_64_NAN = 0xFFFFFFFFFFFFFFFF  # SMA uses this value to represent NaN

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SmaSunnyBoySmartEnergyBatSetup],
                 tcp_client: ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SmaSunnyBoySmartEnergyBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.store.set(self.read())

    def read(self) -> BatState:
        unit = self.component_config.configuration.modbus_id

        soc = self.__tcp_client.read_holding_registers(30845, ModbusDataType.UINT_32, unit=unit)
        current = self.__tcp_client.read_holding_registers(30843, ModbusDataType.INT_32, unit=unit)/-1000
        voltage = self.__tcp_client.read_holding_registers(30851, ModbusDataType.INT_32, unit=unit)/100

        if soc == self.SMA_UINT32_NAN:
            # If the storage is empty and nothing is produced on the DC side, the inverter does not supply any values.
            soc = 0
            power = 0
        else:
            power = current*voltage
        exported = self.__tcp_client.read_holding_registers(31401, ModbusDataType.UINT_64, unit=3)
        imported = self.__tcp_client.read_holding_registers(31397, ModbusDataType.UINT_64, unit=3)

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


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyBoySmartEnergyBatSetup)
