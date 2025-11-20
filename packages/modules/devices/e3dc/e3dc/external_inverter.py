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
from modules.devices.e3dc.e3dc.config import E3dcExternalInverterSetup

log = logging.getLogger(__name__)


def read_external_inverter(client: modbus.ModbusTcpClient_, modbus_id: int) -> int:
    pv_external = int(client.read_holding_registers(
        40075, ModbusDataType.INT_32, wordorder=Endian.Little, device_id=modbus_id))
    return pv_external


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: modbus.ModbusTcpClient_


class E3dcExternalInverter(AbstractInverter):
    def __init__(self, component_config: E3dcExternalInverterSetup, **kwargs: Any) -> None:
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
        pv_external = read_external_inverter(self.client, self.__modbus_id)
        # pv_external - > pv Leistung
        # die als externe Produktion an e3dc angeschlossen ist
        # Im gegensatz zur Implementierung in Version 1.9 wird nicht mehr die PV
        # Leistung vom WR1 gelesen, da die durch v2.0 separat gehandelt wird
        _, pv_exported = self.sim_counter.sim_count(pv_external)
        inverter_state = InverterState(
            power=pv_external,
            exported=pv_exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=E3dcExternalInverterSetup)
