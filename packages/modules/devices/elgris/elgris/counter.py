#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.devices.elgris.elgris.elgris import Elgris
from modules.devices.elgris.elgris.config import ElgrisCounterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.store import get_counter_value_store
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    tcp_client: modbus.ModbusTcpClient_
    modbus_id: int


class ElgrisCounter(AbstractCounter):
    def __init__(self, component_config: ElgrisCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)
        self.elgris = Elgris(self.__modbus_id, self.__tcp_client, self.fault_state)
        self.store = get_counter_value_store(self.component_config.id)

    def update(self):
        counter_state = self.elgris.get_counter_state()
        imported, exported = self.peak_filter.check_values(counter_state.power,
                                                           counter_state.imported,
                                                           counter_state.exported)
        counter_state.imported = imported
        counter_state.exported = exported
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ElgrisCounterSetup)
