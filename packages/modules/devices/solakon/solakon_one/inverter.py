#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.solakon.solakon_one.config import SolakonOneInverterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_id: int


class SolakonOneInverter(AbstractInverter):
    def __init__(self, component_config: SolakonOneInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(
            self.kwargs['device_id'], self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        # Gesamte DC PV Leistung aller vier MPPT in W
        power = self.client.read_holding_registers(39118, ModbusDataType.INT_32, unit=unit) * -1
        # Gesamte DC PV Produktion in Wh
        exported = self.client.read_holding_registers(39601, ModbusDataType.UINT_32, unit=unit) * 10
        # Gerät hat keinen Zähler für AC-seitigen Bezug (z.B. Eigenverbrauch des WR selbst) - simulieren,
        # damit die Hybrid-Berechnung in PurgeInverterState.fix_hybrid_values() einen Wert hat.
        imported, _ = self.sim_counter.sim_count(power)

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        inverter_state = InverterState(
            power=power,
            imported=imported,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolakonOneInverterSetup)
