#!/usr/bin/env python3
import logging
from typing import Any, List, Tuple, TypedDict

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.kostal.kostal_piko.config import KostalPikoCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class KostalPikoCounter(AbstractCounter):
    def __init__(self, component_config: KostalPikoCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def get_values(self) -> Tuple[float, List[float]]:
        params = (('dxsEntries', ['83887106', '83887362', '83887618']),)
        resp = req.get_http_session().get('http://'+self.ip_address+'/api/dxs.json',
                                          params=params,
                                          timeout=3).json()["dxsEntries"]
        powers = [float(resp[0]["value"]), float(resp[1]["value"]), float(resp[2]["value"])]
        home_consumption = sum(powers)
        return home_consumption, powers

    def update(self):
        power, powers = self.get_values()
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPikoCounterSetup)
