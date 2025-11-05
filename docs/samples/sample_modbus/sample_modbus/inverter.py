#!/usr/bin/env python3
from enum import IntEnum
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.sample_modbus.sample_modbus.config import SampleInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class Register(IntEnum):
    CURRENT_L1 = 0x06
    POWER = 0x0C
    DC_POWER = 0x48
    EXPORTED = 0x4A


class SampleInverter(AbstractInverter):
    REG_MAPPING = (
        (Register.CURRENT_L1, [ModbusDataType.FLOAT_32]*3),
        (Register.POWER, [ModbusDataType.FLOAT_32]*3),
        (Register.DC_POWER, ModbusDataType.FLOAT_32),
        (Register.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, component_config: SampleInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        # Modbus-Bulk reader, liest einen Block von Registern und gibt ein Dictionary mit den Werten zurück
        # read_input_registers_bulk benötigit als Parameter das Startregister, die Anzahl der Register,
        # Register-Mapping und die Modbus-ID
        resp = self.client.read_input_registers_bulk(
            Register.CURRENT_L1, 70, mapping=self.REG_MAPPING, unit=self.id)
        inverter_state = InverterState(
            power=resp[Register.POWER],
            currents=resp[Register.CURRENT_L1],
            dc_power=resp[Register.DC_POWER],
            exported=resp[Register.EXPORTED],
        )
        self.store.set(inverter_state)

        # Einzelregister lesen (dauert länger, bei sehr weit >100 auseinanderliegenden Registern sinnvoll)
        power = self.client.read_holding_registers(reg, ModbusDataType.INT_32, unit=unit)
        exported = self.sim_counter.sim_count(power)[1]

        inverter_state = InverterState(
            currents=currents,
            power=power,
            exported=exported,
            dc_power=dc_power
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleInverterSetup)
