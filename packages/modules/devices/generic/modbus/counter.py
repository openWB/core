#!/usr/bin/env python3
from typing import Any, TypedDict
from modules.devices.generic.modbus.helper import read_phase_values, read_value
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.component_type import ComponentDescriptor
from modules.common.simcount._simcounter import SimCounter
from modules.devices.generic.modbus.config import GenericModbusCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

from modules.common.store._factory import get_component_value_store

from modules.common.modbus import ModbusTcpClient_

import logging
log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class GenericModbusCounter(AbstractCounter):
    def __init__(self, component_config: GenericModbusCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        config = self.component_config.configuration

        # Power
        power = read_value(self.client, unit, config.power)
        if power is None:
            raise ValueError("Leistungsregister muss angegeben werden.")

        # Voltages
        voltages_value = read_phase_values(self.client, unit, config.voltage_L1, config.voltage_L2, config.voltage_L3)
        if voltages_value is not None:
            voltages = voltages_value

        # Currents
        currents_value = read_phase_values(self.client, unit, config.current_L1, config.current_L2, config.current_L3)
        if currents_value is not None:
            currents = currents_value

        # Powers
        powers_value = read_phase_values(self.client, unit, config.powers_L1, config.powers_L2, config.powers_L3)
        if powers_value is not None:
            powers = powers_value

        # Power Factors
        power_factors_value = read_phase_values(
            self.client,
            unit,
            config.power_factor_L1,
            config.power_factor_L2,
            config.power_factor_L3,
        )
        if power_factors_value is not None:
            power_factors = power_factors_value

        # Frequency
        frequency_value = read_value(self.client, unit, config.frequency)
        if frequency_value is not None:
            frequency = frequency_value

        # Imported
        imported = read_value(self.client, unit, config.imported)

        # Exported
        exported = read_value(self.client, unit, config.exported)

        # Serial Number
        serial_number_value = read_value(self.client, unit, config.serial_number)
        if serial_number_value is not None:
            serial_number = serial_number_value

        if power is not None:
            self.peak_filter.check_values(power)
            if imported is None or exported is None:
                imported, exported = self.sim_counter.sim_count(power)
            imported, exported = self.peak_filter.check_values(power, imported, exported)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )

        if "voltages" in locals():
            counter_state.voltages = voltages
        if "currents" in locals():
            counter_state.currents = currents
        if "powers" in locals():
            counter_state.powers = powers
        if "power_factors" in locals():
            counter_state.power_factors = power_factors
        if "frequency" in locals():
            counter_state.frequency = frequency
        if "serial_number" in locals():
            counter_state.serial_number = serial_number

        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GenericModbusCounterSetup)
