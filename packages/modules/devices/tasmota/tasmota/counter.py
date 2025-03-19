#!/usr/bin/env python3
from typing import Dict, Union
import logging

from dataclass_utils import dataclass_from_dict
from modules.devices.tasmota.tasmota.config import TasmotaCounterSetup
from modules.common.abstract_device import AbstractCounter
from modules.common.tasmota import Tasmota
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store

log = logging.getLogger(__name__)


class TasmotaCounter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, TasmotaCounterSetup],
                 ip_address: str,
                 phase: int) -> None:
        self.__device_id = device_id
        self.__ip_address = ip_address
        if phase:
            self.__phase = phase
        else:
            self.__phase = 1
        self.component_config = dataclass_from_dict(TasmotaCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)
        self.__tasmota = Tasmota(self.__device_id, self.__ip_address, self.__phase)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        log.debug("tasmota.counter.update: " + self.__ip_address)
        counter_state = self.__tasmota.get_CounterState()
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaCounterSetup)
