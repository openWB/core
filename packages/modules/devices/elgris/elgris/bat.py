#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.component_state import BatState
from modules.devices.elgris.elgris.elgris import Elgris
from modules.devices.elgris.elgris.config import ElgrisBatSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_bat_value_store


class KwargsDict(TypedDict):
    tcp_client: modbus.ModbusTcpClient_
    modbus_id: int


class ElgrisBat(AbstractBat):
    def __init__(self, component_config: ElgrisBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.elgris = Elgris(self.__modbus_id, self.__tcp_client, self.fault_state)
        self.store = get_bat_value_store(self.component_config.id)

    def update(self):
        with self.__tcp_client:
            counter_state = self.elgris.get_counter_state()
        bat_state = BatState(
            exported=counter_state.exported,
            imported=counter_state.imported,
            power=counter_state.power,
            currents=counter_state.currents,
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=ElgrisBatSetup)
