#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.modbus import ModbusTcpClient_
from modules.common.store._factory import get_component_value_store
from modules.devices.generic.modbus.config import GenericModbusInverterSetup
from modules.common.component_type import ComponentType
from modules.common.simcount import SimCounter

from modules.devices.generic.modbus.helper import read_phase_values, read_value


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class GenericModbusInverter(AbstractInverter):
    def __init__(self, component_config: GenericModbusInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, self.component_config.type)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        config = self.component_config.configuration

        # Power
        power = read_value(self.client, unit, config.power)
        if power is None:
            raise ValueError("Leistungsregister muss angegeben werden.")

        # Exported
        exported = read_value(self.client, unit, config.exported)

        # Imported
        imported = read_value(self.client, unit, config.imported)

        # Currents
        currents_value = read_phase_values(self.client, unit, config.current_L1, config.current_L2, config.current_L3)
        if currents_value is not None:
            currents = currents_value

        # DC Power
        dc_power_value = read_value(self.client, unit, config.dc_power)
        if dc_power_value is not None:
            dc_power = dc_power_value

        # Serial Number
        serial_number_value = read_value(self.client, unit, config.serial_number)
        if serial_number_value is not None:
            serial_number = serial_number_value

        if imported is None or exported is None:
            self.peak_filter.check_values(power)
            imported, exported = self.sim_counter.sim_count(power)
        else:
            imported, exported = self.peak_filter.check_values(power, imported, exported)

        inverter_state = InverterState(
            power=power,
            exported=exported,
            imported=imported,
        )

        if "dc_power" in locals():
            inverter_state.dc_power = dc_power
        if "currents" in locals():
            inverter_state.currents = currents
        if "serial_number" in locals():
            inverter_state.serial_number = serial_number

        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GenericModbusInverterSetup)
