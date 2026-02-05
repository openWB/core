#!/usr/bin/env python3
import logging
from typing import Dict, TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeExternalInverterSetup
from modules.devices.solaredge.solaredge.scale import scale_registers
from modules.devices.solaredge.solaredge.meter import SolaredgeMeterRegisters, set_component_registers

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    components: Dict


class SolaredgeExternalInverter(AbstractInverter):
    def __init__(self,
                 component_config: SolaredgeExternalInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client = self.kwargs['client']
        self.registers = SolaredgeMeterRegisters(self.component_config.configuration.meter_id)
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

        components = list(self.kwargs['components'].values())
        components.append(self)
        set_component_registers(self.component_config, self.__tcp_client, components)

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self) -> InverterState:
        reg_mapping = (
            (self.registers.currents, [ModbusDataType.INT_16]*3),
            (self.registers.currents_scale, ModbusDataType.INT_16),
            (self.registers.power, ModbusDataType.INT_16),
            (self.registers.powers_scale, ModbusDataType.INT_16),
            (self.registers.exported, ModbusDataType.UINT_32),
            (self.registers.imp_exp_scale, ModbusDataType.INT_16),
        )
        resp = self.__tcp_client.read_holding_registers_bulk(
            self.registers.currents, 52, mapping=reg_mapping, unit=self.component_config.configuration.modbus_id)

        factor = self.component_config.configuration.factor
        return InverterState(
            exported=scale_registers(resp[self.registers.exported], resp[self.registers.imp_exp_scale]),
            power=scale_registers(resp[self.registers.power], resp[self.registers.powers_scale]) * factor,
            currents=scale_registers(resp[self.registers.currents], resp[self.registers.currents_scale])
        )


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeExternalInverterSetup)
