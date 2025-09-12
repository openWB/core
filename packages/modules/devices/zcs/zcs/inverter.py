#!/usr/bin/env python3
import logging
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.zcs.zcs.config import ZCSInverterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class ZCSInverter(AbstractInverter):
    def __init__(self, component_config: ZCSInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs
        self.__modbus_id = component_config.configuration.modbus_id

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = exported = 0
        currents = None
        try:
            power = self.client.read_holding_registers(0x0485, ModbusDataType.INT_16, unit=self.__modbus_id)*10
            exported = self.client.read_holding_registers(0x0684, ModbusDataType.UINT_32, unit=self.__modbus_id)*10
            currents = [
                self.client.read_holding_registers(0x48E, ModbusDataType.INT_16, unit=self.__modbus_id)*0.01,
                self.client.read_holding_registers(0x499, ModbusDataType.INT_16, unit=self.__modbus_id)*0.01,
                self.client.read_holding_registers(0x4A4, ModbusDataType.INT_16, unit=self.__modbus_id)*0.01
            ]
        except Exception:
            log.debug("Modbus could not be read.")
        
        inverter_state = InverterState(
            currents=currents,
            power=power,
            exported=exported
            # dc_power=dc_power
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ZCSInverterSetup)