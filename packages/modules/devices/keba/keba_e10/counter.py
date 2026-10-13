#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.devices.keba.keba_e10.config import KebaE10CounterSetup


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    modbus_id: int


class KebaE10Counter(AbstractCounter):
    def __init__(self, component_config: KebaE10CounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs["client"]
        self.__modbus_id: int = self.kwargs["modbus_id"]
        from modules.common.store._counter import get_counter_value_store
        from modules.common.utils.peak_filter import PeakFilter
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def __u32(self, address: int) -> int:
        return int(self.__tcp_client.read_holding_registers(
            address, ModbusDataType.UINT_32, unit=self.__modbus_id
        ))

    def __i32(self, address: int) -> int:
        return int(self.__tcp_client.read_holding_registers(
            address, ModbusDataType.INT_32, unit=self.__modbus_id
        ))

    def update(self) -> None:
        # The E10 exposes these values as high-word-first 32-bit Holding Registers.
        # openWB's Modbus wrapper decodes UINT_32 using big-endian word order.
        with self.__tcp_client:
            active_plus = self.__u32(0)
            active_minus = self.__u32(2)

            # Lifetime counters are uint64. Raw/10 yields Wh (raw/10000 yields kWh).
            imported, exported = [
                value / 10.0 for value in self.__tcp_client.read_holding_registers(
                    512, [ModbusDataType.UINT_64, ModbusDataType.UINT_64],
                    unit=self.__modbus_id
                )
            ]

            frequency = self.__u32(26) / 1000.0

            powers = [
                (self.__u32(40) - self.__u32(42)) / 10.0,
                (self.__u32(80) - self.__u32(82)) / 10.0,
                (self.__u32(120) - self.__u32(122)) / 10.0,
            ]
            currents = [
                self.__u32(60) / 1000.0,
                self.__u32(100) / 1000.0,
                self.__u32(140) / 1000.0,
            ]
            voltages = [
                self.__u32(62) / 1000.0,
                self.__u32(102) / 1000.0,
                self.__u32(142) / 1000.0,
            ]
            power_factors = [
                self.__i32(64) / 1000.0,
                self.__i32(104) / 1000.0,
                self.__i32(144) / 1000.0,
            ]

        # Keep import positive and export negative at the EVU point.
        # The E10 gives separate positive/negative registers; subtracting them
        # produces the signed net power used by openWB.
        power = (active_plus - active_minus) / 10.0
        imported, exported = self.peak_filter.check_values(power, imported, exported)

        self.store.set(CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            currents=currents,
            voltages=voltages,
            power_factors=power_factors,
            frequency=frequency
        ))


component_descriptor = ComponentDescriptor(configuration_factory=KebaE10CounterSetup)
