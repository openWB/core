#!/usr/bin/env python3
import logging
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusTcpClient_, ModbusDataType
from modules.common.simcount._simcounter import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.sma.sma_sunny_boy.config import SmaTesvoltBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class TesvoltBat(AbstractBat):
    def __init__(self, component_config: SmaTesvoltBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        soc = self.__tcp_client.read_input_registers(1056, ModbusDataType.INT_32, unit=25) / 10
        power = self.__tcp_client.read_input_registers(1012, ModbusDataType.INT_32, unit=25) * -1
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        log.debug("Bat {}: {}".format(self.__tcp_client.address, bat_state))
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SmaTesvoltBatSetup)
