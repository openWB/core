#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.solakon.solakon_one.config import SolakonOneInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class SolakonOneInverter(AbstractInverter):
    def __init__(self, component_config: SolakonOneInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        # Reg 39134 AC Leistung am Stecker, Batterie aus dem Heimnetz aufladen hat positive Werte,
        # Leistung aus der Batterie und/oder aus PV ins Heimnetz abgeben hat negative Werte
        power = self.client.read_holding_registers(39134, ModbusDataType.INT_32, unit=unit) * -1

        # Gesamte Energie am Wechselrichter in Wh
        exported = self.client.read_holding_registers(39621, ModbusDataType.UINT_32, unit=unit) * 10
        imported = self.client.read_holding_registers(39625, ModbusDataType.UINT_32, unit=unit) * 10

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        inverter_state = InverterState(
            power=power,
            imported=imported,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolakonOneInverterSetup)
