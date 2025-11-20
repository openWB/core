#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.fox_ess.fox_ess.config import FoxEssInverterSetup


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class FoxEssInverter(AbstractInverter):
    def __init__(self, component_config: FoxEssInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        # PV1 + PV2 Power
        power = sum([self.client.read_holding_registers(
            reg, ModbusDataType.INT_16, device_id=unit)
            for reg in [31002, 31005]]) * -1
        # Gesamt Produktion Wechselrichter unsigned integer in kWh * 0,1
        exported = self.client.read_holding_registers(32000, ModbusDataType.UINT_32, device_id=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssInverterSetup)
