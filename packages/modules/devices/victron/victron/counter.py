#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.victron.victron.config import VictronCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusUdpClient_


class VictronCounter(AbstractCounter):
    def __init__(self, component_config: VictronCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__udp_client = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        unit = self.component_config.configuration.modbus_id
        energy_meter = self.component_config.configuration.energy_meter
        with self.__udp_client:
            if energy_meter:
                powers = [
                    self.__udp_client.read_holding_registers(reg, ModbusDataType.INT_32, unit=unit) / 1
                    for reg in [0x3082, 0x3086, 0x308A]]
                currents = [
                    self.__udp_client.read_holding_registers(reg, ModbusDataType.INT_16, unit=unit) / 100
                    for reg in [0x3041, 0x3049, 0x3051]]
                voltages = [
                    self.__udp_client.read_holding_registers(reg, ModbusDataType.INT_16, unit=unit) / 100
                    for reg in [0x3040, 0x3048, 0x3050]]
                power_factors = [
                    self.__udp_client.read_holding_registers(reg, ModbusDataType.INT_16, unit=unit) / 1000
                    for reg in [0x3047, 0x304F, 0x3057]]
                power = sum(powers)
                frequency = self.__udp_client.read_holding_registers(0x3032, ModbusDataType.UINT_16, unit=unit) / 100
            else:
                powers = self.__udp_client.read_holding_registers(820, [ModbusDataType.INT_16]*3, unit=unit)
                power = sum(powers)

        imported, exported = self.sim_counter.sim_count(power)

        if energy_meter:
            counter_state = CounterState(
                voltages=voltages,
                currents=currents,
                powers=powers,
                power_factors=power_factors,
                imported=imported,
                exported=exported,
                power=power,
                frequency=frequency
            )
        else:
            counter_state = CounterState(
                powers=powers,
                imported=imported,
                exported=exported,
                power=power
            )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VictronCounterSetup)
