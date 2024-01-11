#!/usr/bin/env python3
from typing import Dict, Union

from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sungrow.config import SungrowBatSetup, Sungrow


class SungrowBat:
    def __init__(self,
                 device_config: Union[Dict, Sungrow],
                 component_config: Union[Dict, SungrowBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.device_config = device_config
        self.component_config = dataclass_from_dict(SungrowBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.device_config.configuration.modbus_id
        soc = int(self.__tcp_client.read_input_registers(13022, ModbusDataType.INT_16, unit=unit) / 10)
        resp = self.__tcp_client.delegate.read_input_registers(13000, 1, unit=unit)
        binary = bin(resp.registers[0])[2:].zfill(8)
        power = self.__tcp_client.read_input_registers(13021, ModbusDataType.INT_16, unit=unit)
        imported = self.__tcp_client.read_input_registers(13026, ModbusDataType.UINT_32,
                                                          wordorder=Endian.Little, unit=unit) * 100
        exported = self.__tcp_client.read_input_registers(13040, ModbusDataType.UINT_32,
                                                          wordorder=Endian.Little, unit=unit) * 100
        if binary[5] == "1":
            power = power * -1

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SungrowBatSetup)
