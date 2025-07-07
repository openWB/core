#!/usr/bin/env python3
from typing import Any, TypedDict
import logging

from modules.devices.tasmota.tasmota.config import TasmotaInverterSetup
from modules.common.abstract_device import AbstractInverter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.common.simcount import SimCounter
from modules.common import req
from modules.common.component_state import InverterState

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    phase: int


class TasmotaInverter(AbstractInverter):
    def __init__(self, component_config: TasmotaInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        log.debug("Tasmota inverter update: " + self.__ip_address)

        url = "http://" + self.__ip_address + "/cm?cmnd=Status%208"
        response = req.get_http_session().get(url, timeout=5).json()

        if 'ENERGY' in response['StatusSNS']:
            power = float(response['StatusSNS']['ENERGY']['Power']) * -1
            currents = [float(response['StatusSNS']['ENERGY']['Current']), 0.0, 0.0]
            _, exported = self.sim_counter.sim_count(power)

            inverter_state = InverterState(
                power=power,
                currents=currents,
                exported=exported
            )
        else:
            power = float(response['StatusSNS']['Itron']['Power']) * -1
            exported = float(response['StatusSNS']['Itron']['E_out']*1000)

            inverter_state = InverterState(
                power=power,
                exported=exported
            )

        log.debug("Tasmota InverterState:\nurl=" + url +
                  "\nresponse=" + str(response) +
                  "\nInverterState=" + str(inverter_state))
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaInverterSetup)
