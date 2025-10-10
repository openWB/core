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
from modules.devices.solaredge.solaredge.scale import create_scaled_reader
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

        self._read_scaled_int16 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.INT_16
        )
        self._read_scaled_uint32 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.UINT_32
        )

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self) -> InverterState:
        factor = self.component_config.configuration.factor
        power = self._read_scaled_int16(self.registers.powers, 4)[0] * factor
        exported = self._read_scaled_uint32(self.registers.imp_exp, 8)[0]
        currents = self._read_scaled_int16(self.registers.currents, 3)

        return InverterState(
            exported=exported,
            power=power,
            currents=currents
        )


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeExternalInverterSetup)
