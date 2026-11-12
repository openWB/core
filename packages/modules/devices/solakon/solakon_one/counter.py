#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.solakon.solakon_one.config import SolakonOneCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class SolakonOneCounter(AbstractCounter):
    def __init__(self, component_config: SolakonOneCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        # Reg 39134 AC Leistung am Stecker (Grid Information laut Hersteller-Doku), Bezug hat positive Werte,
        # Einspeisung hat negative Werte
        power = self.client.read_holding_registers(39134, ModbusDataType.INT_32, unit=unit) * -1

        # Gesamte Netzeinspeisung/-bezug in Wh
        exported = self.client.read_holding_registers(39621, ModbusDataType.UINT_32, unit=unit) * 10
        imported = self.client.read_holding_registers(39625, ModbusDataType.UINT_32, unit=unit) * 10

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        counter_state = CounterState(
            power=power,
            imported=imported,
            exported=exported
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolakonOneCounterSetup)
