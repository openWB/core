#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solax.solax_gen5.config import SolaxGen5BatSetup


class SolaxGen5Bat(AbstractBat):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaxGen5BatSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.__modbus_id = modbus_id
        self.component_config = dataclass_from_dict(SolaxGen5BatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        with self.__tcp_client:
            power_bat1 = self.__tcp_client.read_input_registers(22, ModbusDataType.INT_16, unit=self.__modbus_id)
            power_bat2 = self.__tcp_client.read_input_registers(297, ModbusDataType.INT_16, unit=self.__modbus_id)
            power = power_bat1 + power_bat2
            try:
                soc = self.__tcp_client.read_input_registers(302, ModbusDataType.UINT_16, unit=self.__modbus_id)
            except Exception:
                soc = self.__tcp_client.read_input_registers(28, ModbusDataType.UINT_16, unit=self.__modbus_id)

            try:
                imported = self.__tcp_client.read_input_registers(35,
                                                                  ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
                exported = self.__tcp_client.read_input_registers(32,
                                                                  ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
            except Exception:
                imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolaxGen5BatSetup)
