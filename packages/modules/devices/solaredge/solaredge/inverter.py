#!/usr/bin/env python3
from enum import IntEnum
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeInverterSetup
from modules.devices.solaredge.solaredge.scale import scale_registers
from modules.common.simcount import SimCounter


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    device_id: int


class Register(IntEnum):
    POWER = 40083
    POWER_SCALE = 40084
    EXPORTED = 40093
    EXPORTED_SCALE = 40095
    CURRENTS = 40072
    CURRENTS_SCALE = 40075
    DC_POWER = 40100
    DC_POWER_SCALE = 40101


class SolaredgeInverter(AbstractInverter):
    REG_MAPPING = (
        (Register.POWER, ModbusDataType.INT_16),
        (Register.POWER_SCALE, ModbusDataType.INT_16),
        (Register.EXPORTED, ModbusDataType.UINT_32),
        (Register.EXPORTED_SCALE, ModbusDataType.INT_16),
        (Register.CURRENTS, [ModbusDataType.UINT_16]*3),
        (Register.CURRENTS_SCALE, ModbusDataType.INT_16),
        (Register.DC_POWER, ModbusDataType.INT_16),
        (Register.DC_POWER_SCALE, ModbusDataType.INT_16),
    )

    def __init__(self,
                 component_config: SolaredgeInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.kwargs['device_id'], self.component_config.id, prefix="Wechselrichter")

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self):
        resp = self.__tcp_client.read_holding_registers_bulk(
            Register.POWER, 18, mapping=self.REG_MAPPING, unit=self.component_config.configuration.modbus_id)

        power = scale_registers(resp[Register.POWER], resp[Register.POWER_SCALE]) * -1
        imported, _ = self.sim_counter.sim_count(power)

        return InverterState(
            power=power,
            exported=scale_registers(resp[Register.EXPORTED], resp[Register.EXPORTED_SCALE]),
            currents=scale_registers(resp[Register.CURRENTS], resp[Register.CURRENTS_SCALE]),
            dc_power=scale_registers(resp[Register.DC_POWER], resp[Register.DC_POWER_SCALE]) * -1,
            imported=imported,
        )


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeInverterSetup)
