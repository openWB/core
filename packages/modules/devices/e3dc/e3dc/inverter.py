#!/usr/bin/env python3
import logging
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType, Endian
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.e3dc.e3dc.config import E3dcInverterSetup

log = logging.getLogger(__name__)


def read_inverter(client: modbus.ModbusTcpClient_, modbus_id: int) -> int:
    pv = int(client.read_holding_registers(40067, ModbusDataType.INT_32, wordorder=Endian.Little, unit=modbus_id) * -1)
    return pv


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: modbus.ModbusTcpClient_


class E3dcInverter(AbstractInverter):
    def __init__(self, component_config: E3dcInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        pv = read_inverter(self.client, self.__modbus_id)
        # Im gegensatz zur Implementierung in Version 1.9 wird nicht mehr die PV
        # Leistung vom WR1 gelesen, da die durch v2.0 separat gehandelt wird
        _, pv_exported = self.sim_counter.sim_count(pv)
        inverter_state = InverterState(
            power=pv,
            exported=pv_exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=E3dcInverterSetup)
