#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import req
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.sample_request_by_component.config import SampleInverterSetup, SampleConfiguration


class SampleInverter:
    def __init__(self, device_id: int, component_config: Union[Dict, SampleInverterSetup], ip_address: str) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SampleInverterSetup, component_config)
        self.ip_address = ip_address
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self) -> None:
        resp = req.get_http_session().get(self.ip_address)
        exported = self.sim_counter.sim_count(power)[1]

        inverter_state = InverterState(
            currents=currents,
            power=power,
            exported=exported,
            dc_power=dc_power
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleInverterSetup)
