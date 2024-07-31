#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.sofar.sofar.config import SofarBatSetup


class SofarBat:
    def __init__(self,
                 component_config: Union[Dict, SofarBatSetup],
                 modbus_id: int) -> None:
        self.__modbus_id = modbus_id
        self.component_config = dataclass_from_dict(SofarBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        # 0x0606 Power_bat1 Int16 in kW accuracy 0,01
        # 0x060D Power_bat2, 0x0614 Power_bat3, 0x061B Power_bat4, 0x0622 Power_bat5,
        # 0x0629 Power_bat6, 0x0630 Power_bat7, 0x0637 Power_bat8
        # 0x0646 Power_bat9, 0x064D Power_bat10, 0x0654 Power_bat11, 0x065B Power_bat12
        power = sum(client.read_input_registers(reg, ModbusDataType.INT_16, unit=self.__modbus_id)
                    for reg in [0x0606, 0x060D, 0x0614, 0x061B, 0x0622, 0x0629, 0x0630,
                                0x0637, 0x0646, 0x064D, 0x0654, 0x065B])
        # 0x0608 SOC_Bat1 UInt16 in % accuracy 1
        # 0x060F SOC_bat2, 0x0616 SOC_bat3, 0x061D SOC_bat4, 0x0624 SOC_bat5,
        # 0x062B SOC_bat6, 0x0632 SOC_bat7, 0x0639 SOC_bat_8
        # 0x0648 SOC_bat9, 0x064F SOC_bat10, 0x0656 SOC_bat11, 0x065D SOC_bat12
        soc = sum(client.read_input_registers(0x0608, ModbusDataType.UINT_16, unit=self.__modbus_id)
                  for reg in [0x0608, 0x060F, 0x0616, 0x061D, 0x0624, 0x062B, 0x0632,
                              0x0639, 0x0648, 0x064F, 0x0656, 0x065D])
        # 0x0696 Bat_charge_total LSB UInt32 0,1 kWh
        # 0x0697 Bat_charge_total UInt32 0,1 kWh
        imported = client.read_input_registers(
            0x0696, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        # 0x069A Bat_discharge_total LSB UInt32 0,1 kWh
        # 0x069B Bat:discharge_total UInt32 0,1 kWh
        exported = client.read_input_registers(
            0x069A, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SofarBatSetup)
