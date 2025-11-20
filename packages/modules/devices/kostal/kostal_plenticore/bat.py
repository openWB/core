#!/usr/bin/env python3
import logging
from typing import TypedDict, Any
from pymodbus.constants import Endian

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.kostal.kostal_plenticore.config import KostalPlenticoreBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    endianess: Endian
    client: ModbusTcpClient_


class KostalPlenticoreBat(AbstractBat):
    def __init__(self, component_config: KostalPlenticoreBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.endianess: Endian = self.kwargs['endianess']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")

    def update(self) -> None:
        power = self.client.read_holding_registers(
            582, ModbusDataType.INT_16, device_id=self.modbus_id, wordorder=self.endianess) * -1
        soc = self.client.read_holding_registers(
            514, ModbusDataType.INT_16, device_id=self.modbus_id, wordorder=self.endianess)
        if power < 0:
            power = self.client.read_holding_registers(
                106, ModbusDataType.FLOAT_32, device_id=self.modbus_id, wordorder=self.endianess) * -1
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPlenticoreBatSetup)
