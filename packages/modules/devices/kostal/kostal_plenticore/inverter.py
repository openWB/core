#!/usr/bin/env python3
from typing import TypedDict, Any
from pymodbus.constants import Endian

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.kostal.kostal_plenticore.config import KostalPlenticoreInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    endianess: Endian
    client: ModbusTcpClient_


class KostalPlenticoreInverter(AbstractInverter):
    def __init__(self, component_config: KostalPlenticoreInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.endianess: Endian = self.kwargs['endianess']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="Wechselrichter")

    def update(self) -> None:
        power = self.client.read_holding_registers(
            575, ModbusDataType.INT_16, unit=self.modbus_id, wordorder=self.endianess) * -1
        exported = self.client.read_holding_registers(
            320, ModbusDataType.FLOAT_32, unit=self.modbus_id, wordorder=self.endianess)
        # Try to read dc_power, if it fails just skip it and set to 0
        try:
            dc_power = self.client.read_holding_registers(
                1066, ModbusDataType.FLOAT_32, unit=self.modbus_id, wordorder=self.endianess) * -1
        except Exception:
            dc_power = None
        imported, _ = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            exported=exported,
            dc_power=dc_power,
            imported=imported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPlenticoreInverterSetup)
