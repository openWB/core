#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.anker.smartmeter_gen2.config import AnkerMeter, AnkerMeterCounterSetup


class KwargsDict(TypedDict):
    device_config: AnkerMeter
    client: ModbusTcpClient_


class AnkerMeterCounter(AbstractCounter):
    def __init__(self, component_config: AnkerMeterCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: AnkerMeter = self.kwargs['device_config']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self):
        unit = self.device_config.configuration.modbus_id

        power = self.client.read_input_registers(10644, ModbusDataType.INT_32,
                                                 wordorder=Endian.Big, unit=unit)
        powers = self.client.read_input_registers(10638, [ModbusDataType.INT_32] * 3,
                                                  wordorder=Endian.Big, unit=unit)
        voltages = self.client.read_input_registers(10632, [ModbusDataType.UINT_16] * 3,
                                                    wordorder=Endian.Big, unit=unit)
        currents = self.client.read_input_registers(10635, [ModbusDataType.INT_16] * 3,
                                                    wordorder=Endian.Big, unit=unit)

        # Currents hat keine eigene Vorzeichen (getestet), daher kommen die Vorzeichen aus
        # den powers-Werten

        voltages = [value / 10 for value in voltages]
        currents = [abs(c) / 100 * (1 if p >= 0 else -1) for c, p in zip(currents, powers)]

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages,
            currents=currents
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AnkerMeterCounterSetup)
