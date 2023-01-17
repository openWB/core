#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common import req
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.sample_request_by_component.config import SampleCounterSetup, SampleConfiguration


class SampleCounter:
    def __init__(self, device_id: int, component_config: SampleCounterSetup, ip_address: str) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SampleCounterSetup, component_config)
        self.ip_address = ip_address
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self):
        resp = req.get_http_session().get(self.ip_address)
        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency,
            power_factors=power_factors,
            powers=powers,
            voltages=voltages
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleCounterSetup)
