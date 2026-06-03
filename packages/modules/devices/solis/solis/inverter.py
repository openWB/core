#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.solis.solis.config import SolisInverterSetup
from modules.devices.solis.solis.version import SolisVersion
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_id: int


class SolisInverter:
    def __init__(self, component_config: SolisInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        version = SolisVersion(self.component_config.configuration.version)

        if version == SolisVersion.inverter:
            # Für Stringwechselrichter -1 bei Modbus Registers
            power = self.client.read_input_registers(3004, ModbusDataType.INT_32, unit=unit) * -1
            dc_power = self.client.read_input_registers(3006, ModbusDataType.UINT_32, unit=unit) * -1
            currents = self.client.read_input_registers(3036, [ModbusDataType.UINT_16]*3, unit=unit)
        elif version in (SolisVersion.hybrid, SolisVersion.hybrid_s):
            power = self.client.read_input_registers(33079, ModbusDataType.INT_32, unit=unit) * -1
            dc_power = self.client.read_input_registers(33057, ModbusDataType.UINT_32, unit=unit) * -1
            currents = self.client.read_input_registers(33076, [ModbusDataType.UINT_16]*3, unit=unit)

        currents = [value * -0.1 for value in currents]

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        inverter_state = InverterState(
            power=power,
            dc_power=dc_power,
            currents=currents,
            imported=imported,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolisInverterSetup)
