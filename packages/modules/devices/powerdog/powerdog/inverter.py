#!/usr/bin/env python3
import logging
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.powerdog.powerdog.config import PowerdogInverterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_
    modbus_id: int


class PowerdogInverter(AbstractInverter):
    def __init__(self, component_config: PowerdogInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> float:
        with self.__tcp_client:
            power = self.__tcp_client.read_input_registers(40002, ModbusDataType.INT_32, unit=self.__modbus_id) * -1

        _, exported = self.sim_counter.sim_count(power)
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)
        return power


component_descriptor = ComponentDescriptor(configuration_factory=PowerdogInverterSetup)
