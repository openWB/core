#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.solis.solis.config import SolisInverterSetup
from modules.devices.solis.solis.version import SolisVersion


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    version: SolisVersion


class SolisInverter:
    def __init__(self, component_config: SolisInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.version: SolisVersion = self.kwargs['version']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        if self.version == SolisVersion.inverter:
            power = self.client.read_input_registers(3004, ModbusDataType.UINT_32, unit=unit) * -1
            exported = self.client.read_input_registers(3008, ModbusDataType.UINT_32, unit=unit) * 1000
        elif self.version == SolisVersion.hybrid:
            power = self.client.read_input_registers(33057, ModbusDataType.UINT_32, unit=unit) * -1
            exported = self.client.read_input_registers(33029, ModbusDataType.UINT_32, unit=unit) * 1000

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolisInverterSetup)
