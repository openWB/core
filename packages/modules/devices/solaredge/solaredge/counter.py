#!/usr/bin/env python3
import logging
from typing import Dict, TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeCounterSetup
from modules.devices.solaredge.solaredge.scale import scale_registers
from modules.devices.solaredge.solaredge.meter import SolaredgeMeterRegisters, set_component_registers

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    components: Dict


class SolaredgeCounter(AbstractCounter):
    def __init__(self, component_config: SolaredgeCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.registers = SolaredgeMeterRegisters()
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

        components = list(self.kwargs['components'].values())
        components.append(self)
        set_component_registers(self.component_config, self.__tcp_client, components)

    def update(self):
        reg_mapping = (
            (self.registers.voltages, [ModbusDataType.INT_16]*3),
            (self.registers.voltages_scale, ModbusDataType.INT_16),
            (self.registers.currents, [ModbusDataType.INT_16]*3),
            (self.registers.currents_scale, ModbusDataType.INT_16),
            (self.registers.powers, [ModbusDataType.INT_16]*3),
            (self.registers.power, ModbusDataType.INT_16),
            (self.registers.powers_scale, ModbusDataType.INT_16),
            (self.registers.power_factors, [ModbusDataType.INT_16]*3),
            (self.registers.power_factors_scale, ModbusDataType.INT_16),
            (self.registers.frequency, ModbusDataType.INT_16),
            (self.registers.frequency_scale, ModbusDataType.INT_16),
            (self.registers.imported, ModbusDataType.UINT_32),
            (self.registers.exported, ModbusDataType.UINT_32),
            (self.registers.imp_exp_scale, ModbusDataType.INT_16),
        )
        resp = self.__tcp_client.read_holding_registers_bulk(
            self.registers.currents, 52, mapping=reg_mapping, unit=self.component_config.configuration.modbus_id)

        counter_state = CounterState(
            imported=scale_registers(resp[self.registers.imported], resp[self.registers.imp_exp_scale]),
            exported=scale_registers(resp[self.registers.exported], resp[self.registers.imp_exp_scale]),
            power=scale_registers(resp[self.registers.power], resp[self.registers.powers_scale]) * -1,
            powers=[-power for power in scale_registers(resp[self.registers.powers],
                                                        resp[self.registers.powers_scale])],
            voltages=scale_registers(resp[self.registers.voltages], resp[self.registers.voltages_scale]),
            currents=scale_registers(resp[self.registers.currents], resp[self.registers.currents_scale]),
            power_factors=[power_factor / 100 for power_factor in scale_registers(
                resp[self.registers.power_factors], resp[self.registers.power_factors_scale])],
            frequency=scale_registers(resp[self.registers.frequency], resp[self.registers.frequency_scale]),
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeCounterSetup)
