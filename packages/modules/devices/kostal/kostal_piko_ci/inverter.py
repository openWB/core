#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.kostal.kostal_piko_ci.config import KostalPikoCiInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class KostalPikoCiInverter(AbstractInverter):
    def __init__(self, component_config: KostalPikoCiInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_holding_registers(172, ModbusDataType.FLOAT_32, unit=unit) * -1
        currents = [self.client.read_holding_registers(
            reg, ModbusDataType.FLOAT_32, unit=unit) for reg in [154, 160, 166]]
        exported = self.client.read_holding_registers(320, ModbusDataType.FLOAT_32, unit=unit)

        inverter_state = InverterState(
            power=power,
            currents=currents,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPikoCiInverterSetup)
