#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common import req
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sample_request_by_component.config import SampleBatSetup, SampleConfiguration


class SampleBat:
    def __init__(self, device_id: int, component_config: SampleBatSetup, ip_address: str) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SampleBatSetup, component_config)
        self.ip_address = ip_address
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self) -> None:
        resp = req.get_http_session().get(self.ip_address)
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=SampleBatSetup)
