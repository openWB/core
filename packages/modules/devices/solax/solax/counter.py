#!/usr/bin/env python3
from typing import Dict, Union
from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.devices.solax.solax.config import SolaxCounterSetup, Solax
from modules.devices.solax.solax.version import SolaxVersion


class SolaxCounter(AbstractCounter):
    def __init__(self,
                 device_config: Union[Dict, Solax],
                 component_config: Union[Dict, SolaxCounterSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.device_config = device_config
        self.component_config = dataclass_from_dict(SolaxCounterSetup, component_config)
        self.__tcp_client = tcp_client
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        unit = self.device_config.configuration.modbus_id
        with self.__tcp_client:
            if SolaxVersion(self.device_config.configuration.version) == SolaxVersion.g3:
                power = self.__tcp_client.read_input_registers(70, ModbusDataType.INT_32, wordorder=Endian.Little,
                                                               unit=unit) * -1
                frequency = self.__tcp_client.read_input_registers(7, ModbusDataType.UINT_16, unit=unit) / 100
                try:
                    powers = [-value for value in self.__tcp_client.read_input_registers(
                        130, [ModbusDataType.INT_32] * 3, wordorder=Endian.Little, unit=unit
                    )]
                except Exception:
                    powers = None
                exported, imported = [value * 10
                                      for value in self.__tcp_client.read_input_registers(
                                          72, [ModbusDataType.UINT_32] * 2, wordorder=Endian.Little, unit=unit
                                          )]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolaxCounterSetup)
