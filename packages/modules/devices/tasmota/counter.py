#!/usr/bin/env python3
from typing import Dict, Union
import logging

from dataclass_utils import dataclass_from_dict
from modules.devices.tasmota.config import TasmotaCounterSetup
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_counter_value_store

log = logging.getLogger(__name__)


class TasmotaCounter:
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, TasmotaCounterSetup],
                 url: str) -> None:
        self.__device_id = device_id
        self.__url = url
        self.component_config = dataclass_from_dict(TasmotaCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, response: str):
        log.debug("tasmota.counter.update: " + self.__url + ", response=\n" + str(response))
        voltages = [float(response['StatusSNS']['ENERGY']['Voltage']), 0.0, 0.0]
        powers = [float(response['StatusSNS']['ENERGY']['Power']), 0.0, 0.0]
        power = sum(powers)
        currents = [float(response['StatusSNS']['ENERGY']['Current']), 0.0, 0.0]
        power_factors = [float(response['StatusSNS']['ENERGY']['Factor']), 0.0, 0.0]
        frequency = 50.0
        imported = float(response['StatusSNS']['ENERGY']['Total']*1000)
        exported = 0.0

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            voltages=voltages,
            currents=currents,
            powers=powers,
            power_factors=power_factors,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaCounterSetup)
