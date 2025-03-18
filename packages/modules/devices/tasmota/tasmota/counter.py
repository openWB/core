#!/usr/bin/env python3
from typing import Any, TypedDict
import logging

from modules.devices.tasmota.tasmota.config import TasmotaCounterSetup
from modules.common.abstract_device import AbstractCounter
from modules.common.tasmota import Tasmota
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    phase: int


class TasmotaCounter(AbstractCounter):
    def __init__(self, component_config: TasmotaCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__ip_address: str = self.kwargs['ip_address']
        self.__phase: int = self.kwargs['phase']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__tasmota = Tasmota(self.__device_id, self.__ip_address, self.__phase)

    def update(self):
        log.debug("tasmota.counter.update: " + self.__ip_address)
        counter_state = self.__tasmota.get_CounterState()
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaCounterSetup)
