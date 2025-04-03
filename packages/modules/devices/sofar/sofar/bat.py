#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.sofar.sofar.config import SofarBatSetup


class SofarBat(AbstractBat):
    def __init__(self,
                 component_config: Union[Dict, SofarBatSetup],
                 modbus_id: int) -> None:
        self.__modbus_id = modbus_id
        self.component_config = dataclass_from_dict(SofarBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        # 0x900D High 8 bits: the number of battery packs in parallel
        # Lower 8 bits: the number of battery strings in the battery pack
        battery_packs = client.read_holding_registers(0x900D, ModbusDataType.UINT_16, unit=self.__modbus_id) >> 8
        # Power bat1 - bat12: INT_16 in kW accuracy 0,01
        power_regs = [0x0606, 0x060D, 0x0614, 0x061B, 0x0622, 0x0629, 0x0630, 0x0637, 0x0646, 0x064D, 0x0654, 0x065B]

        power = sum(client.read_holding_registers(power_regs[idx], ModbusDataType.INT_16, unit=self.__modbus_id)
                    for idx in range(battery_packs)) * 10
        soc = client.read_holding_registers(0x9012, ModbusDataType.UINT_16, unit=self.__modbus_id)
        # 0x0696 Bat_charge_total LSB UInt32 0,1 kWh
        # 0x0697 Bat_charge_total UInt32 0,1 kWh
        imported = client.read_holding_registers(
            0x0696, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
        # 0x069A Bat_discharge_total LSB UInt32 0,1 kWh
        # 0x069B Bat:discharge_total UInt32 0,1 kWh
        exported = client.read_holding_registers(
            0x069A, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SofarBatSetup)
