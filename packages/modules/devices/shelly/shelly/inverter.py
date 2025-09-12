#!/usr/bin/env python3
import logging
from typing import Optional, TypedDict, Any
from modules.common import req
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.shelly.config import ShellyInverterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    factor: int
    phase: int
    generation: Optional[int]


class ShellyInverter(AbstractInverter):
    def __init__(self, component_config: ShellyInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.address: str = self.kwargs['ip_address']
        self.factor: int = self.kwargs['factor']
        self.phase: int = self.kwargs['phase']
        self.generation: Optional[int] = self.kwargs['generation']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = 0
        if self.generation == 1:
            status_url = "http://" + self.address + "/status"
        else:
            status_url = "http://" + self.address + "/rpc/Shelly.GetStatus"
        status = req.get_http_session().get(status_url, timeout=3).json()
        try:
            alphabetical_index = ['a', 'b', 'c']
            currents = [0.0, 0.0, 0.0]
            # GEN 1
            if "meters" in status:
                meters = status['meters']  # einphasiger shelly?
                for i in range(len(meters)):
                    currents[(i+self.phase-1) % 3] += ((float(meters[i]['power']) * self.factor) / 230
                                                       if meters[i].get('power') else 0)
                    power = power + (float(meters[i]['power'] * self.factor))
            elif "emeters" in status:
                meters = status['emeters']  # shellyEM & shelly3EM
                # shellyEM has one meter, shelly3EM has three meters
                for i in range(0, 3):
                    currents[(i+self.phase-1) % 3] = (float(meters[i]['current']) * self.factor
                                                      if meters[i].get('current') else 0)
                    power = power + (float(meters[i]['power'] * self.factor))
            # GEN 2+
            # shelly Pro3EM
            elif "em:0" in status:
                meters = status['em:0']
                for i in range(0, 3):
                    currents[(i+self.phase-1) % 3] = (float(meters[f'{alphabetical_index[i]}_current']) * self.factor
                                                      if meters.get(f'{alphabetical_index[i]}_current') else 0)
                power = float(meters['total_act_power']) * self.factor
            # Shelly MiniPM G3
            elif "pm1:0" in status:
                log.debug("single phase shelly")
                meters = status['pm1:0']
                currents[self.phase-1] = meters['current'] * self.factor
                power = meters['apower'] * self.factor
            elif 'switch:0' in status and 'apower' in status['switch:0']:
                log.debug("single phase shelly")
                meters = status['switch:0']
                currents[self.phase-1] = meters['current'] * self.factor
                power = meters['apower'] * self.factor
            else:
                log.debug("single phase shelly")
                meters = status['em1:0']
                currents[self.phase-1] = meters['current'] * self.factor
                power = meters['act_power'] * self.factor  # shelly Pro EM Gen 2
            _, exported = self.sim_counter.sim_count(power)

            inverter_state = InverterState(
                power=power,
                currents=currents,
                exported=exported
            )
            self.store.set(inverter_state)
        except KeyError:
            log.exception("unsupported shelly device.")


component_descriptor = ComponentDescriptor(configuration_factory=ShellyInverterSetup)
