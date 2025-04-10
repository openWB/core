#!/usr/bin/env python3
from typing import Any, TypedDict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.solis.solis.config import SolisCounterSetup
from modules.devices.solis.solis.version import SolisVersion


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    version: SolisVersion


class SolisCounter:
    def __init__(self, component_config: SolisCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.version: SolisVersion = self.kwargs['version']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.version = self.kwargs['version']
        self.client = self.kwargs['client']

    def update(self):
        unit = self.component_config.configuration.modbus_id

        register_offset = 30000
        if self.version == SolisVersion.inverter:
            register_offset = -1

        power = self.client.read_input_registers(3263 + register_offset, ModbusDataType.INT_32, unit=unit)
        powers = self.client.read_input_registers(3257 + register_offset, [ModbusDataType.INT_32]*3, unit=unit)
        frequency = self.client.read_input_registers(3282 + register_offset, ModbusDataType.UINT_16, unit=unit) / 100
        imported = self.client.read_input_registers(3283 + register_offset, ModbusDataType.UINT_32, unit=unit) * 10
        exported = self.client.read_input_registers(3285 + register_offset, ModbusDataType.UINT_32, unit=unit) * 10

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolisCounterSetup)
