#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.sofar.sofar.config import SofarInverterSetup


class SofarInverter:
    def __init__(self,
                 component_config: Union[Dict, SofarInverterSetup],
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(SofarInverterSetup, component_config)
        self.__modbus_id = modbus_id
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        # 0x0586 Power_PV1 UInt16 in kW accuracy 0,01
        # 0x0589 Power_PV2, 0x058C Power_PV3, 0x058F Power_PV4, 0x0592 Power_PV5,
        # 0x0595 Power_PV6, 0x0598 Power_PV7, 0x059B Power_PV8, 0x059E Power_PV9, 0x05A1 Power_PV10,
        # 0x05A4 Power_PV11, 0x05A7 Power_PV12, 0x05AA Power_PV13,
        # 0x05AD Power_PV14, 0x05B0 Power_PV15, 0x05B3 Power_PV16
        power = sum([client.read_input_registers(reg, ModbusDataType.UINT_16,
                    unit=self.__modbus_id) for reg in [0x0586, 0x0589, 0x058C, 0x058F, 0x0592,
                                                       0x0595, 0x0598, 0x059B, 0x059E, 0x05A1, 0x05A4,
                                                       0x05A7, 0x05AA, 0x05AD, 0x05B0, 0x05B3]]) * -1
        # 0x05C4 Power_PV_Total UInt16 in kW accuracy 0,1
        # 0x0686 PV_Generation_Total UInt32 0,1 kW LSB
        # 0x0687 PV_Generation_Total UInt32 0,1 kW
        exported = client.read_input_registers(0x0686, ModbusDataType.UINT_32, wordorder=Endian.Little,
                                               unit=self.__modbus_id) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SofarInverterSetup)
