#!/usr/bin/env python3
from typing import Any, TypedDict
import logging

from modules.devices.tasmota.tasmota.config import TasmotaBatSetup
from modules.common.abstract_device import AbstractBat
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount import SimCounter
from modules.common import req
from modules.common.component_state import BatState

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    phase: int


class TasmotaBat(AbstractBat):
    def __init__(self, component_config: TasmotaBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.__phase: int = self.kwargs['phase']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        url = "http://" + self.__ip_address + "/cm?cmnd=Status%208"
        response = req.get_http_session().get(url, timeout=5).json()

        if 'ENERGY' in response['StatusSNS']:
            currents = [0.0, 0.0, 0.0]

            power = float(response['StatusSNS']['ENERGY']['Power'])
            currents[self.__phase-1] = (response['StatusSNS']['ENERGY']['Current']), 0.0, 0.0
            imported = float(response['StatusSNS']['ENERGY']['Total']*1000)
            _, exported = self.sim_counter.sim_count(power)

            bat_state = BatState(
                power=power,
                currents=currents,
                imported=imported,
                exported=exported
            )
        else:
            power = float(response['StatusSNS']['Itron']['Power'])
            imported = float(response['StatusSNS']['Itron']['E_in']*1000)
            exported = float(response['StatusSNS']['Itron']['E_out']*1000)

            bat_state = BatState(
                power=power,
                imported=imported,
                exported=exported
            )

        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaBatSetup)
