#!/usr/bin/env python3
from enum import IntEnum
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.sample_modbus.sample_modbus.config import SampleCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class Register(IntEnum):
    VOLTAGE_L1 = 0x00
    CURRENT_L1 = 0x06
    POWER_L1 = 0x0C
    POWER_FACTOR_L1 = 0x1E
    FREQUENCY = 0x46
    IMPORTED = 0x48
    EXPORTED = 0x4A


class SampleCounter(AbstractCounter):
    REG_MAPPING = (
        (Register.VOLTAGE_L1, [ModbusDataType.FLOAT_32]*3),
        (Register.CURRENT_L1, [ModbusDataType.FLOAT_32]*3),
        (Register.POWER_L1, [ModbusDataType.FLOAT_32]*3),
        (Register.POWER_FACTOR_L1, [ModbusDataType.FLOAT_32]*3),
        (Register.FREQUENCY, ModbusDataType.FLOAT_32),
        (Register.IMPORTED, ModbusDataType.FLOAT_32),
        (Register.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, component_config: SampleCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        unit = self.component_config.configuration.modbus_id
        # Modbus-Bulk reader, liest einen Block von Registern und gibt ein Dictionary mit den Werten zurück
        # read_input_registers_bulk benötigit als Parameter das Startregister, die Anzahl der Register,
        # Register-Mapping und die Modbus-ID
        resp = self.client.read_input_registers_bulk(
            Register.VOLTAGE_L1, 76, mapping=self.REG_MAPPING, unit=self.id)
        counter_state = CounterState(
            imported=resp[Register.IMPORTED],
            exported=resp[Register.EXPORTED],
            power=sum(resp[Register.POWER_L1]),
            voltages=resp[Register.VOLTAGE_L1],
            currents=resp[Register.CURRENT_L1],
            powers=resp[Register.POWER_L1],
            power_factors=resp[Register.POWER_FACTOR_L1],
            frequency=resp[Register.FREQUENCY],
        )
        self.store.set(counter_state)

        # Einzelregister lesen (dauert länger, bei sehr weit >100 auseinanderliegenden Registern sinnvoll)
        power = self.client.read_holding_registers(reg, ModbusDataType.INT_32, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency,
            power_factors=power_factors,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleCounterSetup)
