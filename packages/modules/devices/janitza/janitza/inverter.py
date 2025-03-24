#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.janitza.janitza.config import JanitzaInverterSetup


class JanitzaInverter(AbstractInverter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, JanitzaInverterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(JanitzaInverterSetup, component_config)
        self.__tcp_client = tcp_client
        self.__modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        power = self.__tcp_client.read_holding_registers(19026, ModbusDataType.FLOAT_32, unit=self.__modbus_id) * -1
        _, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=JanitzaInverterSetup)
