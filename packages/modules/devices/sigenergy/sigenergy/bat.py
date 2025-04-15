#!/usr/bin/env python3
import logging
from typing import TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sigenergy.sigenergy.config import SigenergyBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SigenergyBat(AbstractBat):
    def __init__(self, component_config: SigenergyBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_holding_registers(30037, ModbusDataType.INT_32, unit=unit)
        # soc unit 0.1%
        soc = self.client.read_holding_registers(30014, ModbusDataType.UINT_16, unit=unit) / 10
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SigenergyBatSetup)
