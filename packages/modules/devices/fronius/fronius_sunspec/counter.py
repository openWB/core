#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.utils.peak_filter import PeakFilter
from modules.common.store import get_component_value_store
from modules.devices.fronius.fronius_sunspec.config import FroniusSunspecConfiguration, FroniusSunspecCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_
    device_config: FroniusSunspecConfiguration


class FroniusSunspecCounter(AbstractCounter):
    def __init__(self, component_config: FroniusSunspecCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.device_config: FroniusSunspecConfiguration = self.kwargs['device_config']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        unit = self.device_config.counter_modbus_id

        power = self.__tcp_client.read_holding_registers(40098, ModbusDataType.FLOAT_32, unit=unit) * -1  # W
        powers = [
            self.__tcp_client.read_holding_registers(40100, ModbusDataType.FLOAT_32, unit=unit) * -1,  # WphA
            self.__tcp_client.read_holding_registers(40102, ModbusDataType.FLOAT_32, unit=unit) * -1,  # WphB
            self.__tcp_client.read_holding_registers(40104, ModbusDataType.FLOAT_32, unit=unit) * -1,  # WphC
        ]
        currents = [
            self.__tcp_client.read_holding_registers(40074, ModbusDataType.FLOAT_32, unit=unit),  # AphA
            self.__tcp_client.read_holding_registers(40076, ModbusDataType.FLOAT_32, unit=unit),  # AphB
            self.__tcp_client.read_holding_registers(40078, ModbusDataType.FLOAT_32, unit=unit),  # AphC
        ]
        voltages = [
            self.__tcp_client.read_holding_registers(40082, ModbusDataType.FLOAT_32, unit=unit),  # PhVphA
            self.__tcp_client.read_holding_registers(40084, ModbusDataType.FLOAT_32, unit=unit),  # PhVphB
            self.__tcp_client.read_holding_registers(40086, ModbusDataType.FLOAT_32, unit=unit),  # PhVphC
        ]
        power_factors = [
            self.__tcp_client.read_holding_registers(40124, ModbusDataType.FLOAT_32, unit=unit),  # PFphA
            self.__tcp_client.read_holding_registers(40126, ModbusDataType.FLOAT_32, unit=unit),  # PFphB
            self.__tcp_client.read_holding_registers(40128, ModbusDataType.FLOAT_32, unit=unit),  # PFphC
        ]
        frequency = self.__tcp_client.read_holding_registers(40096, ModbusDataType.FLOAT_32, unit=unit)  # Hz
        exported = self.__tcp_client.read_holding_registers(40130, ModbusDataType.FLOAT_32, unit=unit)  # TotWhExp
        imported = self.__tcp_client.read_holding_registers(40138, ModbusDataType.FLOAT_32, unit=unit)  # TotWhImp

        self.peak_filter.check_values(power)
        self.store.set(CounterState(
            power=power,
            powers=powers,
            currents=currents,
            voltages=voltages,
            power_factors=power_factors,
            frequency=frequency,
            imported=imported,
            exported=exported,
        ))


component_descriptor = ComponentDescriptor(configuration_factory=FroniusSunspecCounterSetup)
