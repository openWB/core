#!/usr/bin/env python3
import logging
from typing import Any, Tuple, TypedDict

from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.kostal.kostal_piko.config import KostalPikoBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class KostalPikoBat(AbstractBat):
    def __init__(self, component_config: KostalPikoBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def get_values(self) -> Tuple[float, float]:
        # Bat Current, Bat Voltage, Bat SoC
        params = (('dxsEntries', ['33556225', '33556226', '33556229']),)
        resp = req.get_http_session().get('http://'+self.ip_address+'/api/dxs.json',
                                          params=params,
                                          timeout=3).json()["dxsEntries"]
        power = float(resp[0]["value"]) * float(resp[1]["value"])
        soc = float(resp[2]["value"])
        return power, soc

    def update(self):
        power, soc = self.get_values()

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            imported=imported,
            exported=exported,
            power=power,
            soc=soc
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPikoBatSetup)
