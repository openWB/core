#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.devices.siemens.siemens_sentron.config import SiemensSentronCounterSetup


class SiemensSentronCounter(AbstractCounter):
    def __init__(self,
                 component_config: Union[Dict, SiemensSentronCounterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:
        self.component_config = dataclass_from_dict(SiemensSentronCounterSetup, component_config)
        self.__tcp_client = tcp_client
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.__tcp_client:
            imported = self.__tcp_client.read_holding_registers(801, ModbusDataType.FLOAT_64, unit=self.__modbus_id)
            exported = self.__tcp_client.read_holding_registers(809, ModbusDataType.FLOAT_64, unit=self.__modbus_id)
            power = self.__tcp_client.read_holding_registers(65, ModbusDataType.FLOAT_32, unit=self.__modbus_id)
            powers = self.__tcp_client.read_holding_registers(25, [ModbusDataType.FLOAT_32] * 3, unit=self.__modbus_id)
            frequency = self.__tcp_client.read_holding_registers(55, ModbusDataType.FLOAT_32, unit=self.__modbus_id)
            currents = self.__tcp_client.read_holding_registers(
                13, [ModbusDataType.FLOAT_32] * 3, unit=self.__modbus_id)
            voltages = self.__tcp_client.read_holding_registers(1, [ModbusDataType.FLOAT_32] * 3, unit=self.__modbus_id)
            power_factors = self.__tcp_client.read_holding_registers(
                37, [ModbusDataType.FLOAT_32] * 3, unit=self.__modbus_id)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            currents=currents,
            voltages=voltages,
            frequency=frequency,
            power_factors=power_factors
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SiemensSentronCounterSetup)
