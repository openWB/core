#!/usr/bin/env python3
import logging
from typing import Optional, TypedDict, Any
from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.shelly.config import ShellyCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    factor: int
    phase: int
    generation: Optional[int]


class ShellyCounter(AbstractCounter):
    def __init__(self, component_config: ShellyCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.address: str = self.kwargs['ip_address']
        self.factor: int = self.kwargs['factor']
        self.phase: int = self.kwargs['phase']
        self.generation: Optional[int] = self.kwargs['generation']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = 0
        if self.generation == 1:
            status_url = "http://" + self.address + "/status"
        else:
            status_url = "http://" + self.address + "/rpc/Shelly.GetStatus"
        status = req.get_http_session().get(status_url, timeout=3).json()
        try:
            # GEN 1
            alphabetical_index = ['a', 'b', 'c']
            if "meters" in status:
                powers = [0.0, 0.0, 0.0]
                voltages = [0.0, 0.0, 0.0]
                meters = status['meters']  # einphasiger shelly?
                for i in range(len(meters)):
                    powers[(i+self.phase-1) % 3] = (float(meters[i]['power']) * self.factor
                                                    if meters[i].get('power') else 0)
                    voltages[(i+self.phase-1) % 3] = 230
                power = sum(powers)
            elif "emeters" in status:
                powers = [0.0, 0.0, 0.0]
                currents = [0.0, 0.0, 0.0]
                voltages = [0.0, 0.0, 0.0]
                power_factors = [0.0, 0.0, 0.0]
                meters = status['emeters']  # shellyEM & shelly3EM
                # shellyEM has one meter, shelly3EM has three meters
                for i in range(len(meters)):
                    powers[(i+self.phase-1) % 3] = (float(meters[i]['power']) * self.factor
                                                    if meters[i].get('power') else 0)
                    currents[(i+self.phase-1) % 3] = (float(meters[i]['current']) * self.factor
                                                      if meters[i].get('current') else 0)
                    voltages[(i+self.phase-1) % 3] = (float(meters[i]['voltage'])
                                                      if meters[i].get('voltage') else 0)
                    power_factors[(i+self.phase-1) % 3] = (float(meters[i]['pf'])
                                                           if meters[i].get('pf') else 0)
                power = sum(powers)

            # GEN 2+
            # shelly Pro3EM
            elif "em:0" in status:
                powers = [0.0, 0.0, 0.0]
                currents = [0.0, 0.0, 0.0]
                voltages = [0.0, 0.0, 0.0]
                power_factors = [0.0, 0.0, 0.0]
                meters = status['em:0']
                for i in range(0, 3):
                    if meters.get(f'{alphabetical_index[i]}_act_power') is None:
                        continue
                    powers[(i+self.phase-1) % 3] = (float(meters[f'{alphabetical_index[i]}_act_power']) * self.factor
                                                    if meters.get(f'{alphabetical_index[i]}_act_power') else 0)
                    voltages[(i+self.phase-1) % 3] = (float(meters[f'{alphabetical_index[i]}_voltage'])
                                                      if meters.get(f'{alphabetical_index[i]}_voltage') else 0)
                    currents[(i+self.phase-1) % 3] = (float(meters[f'{alphabetical_index[i]}_current']) * self.factor
                                                      if meters.get(f'{alphabetical_index[i]}_current') else 0)
                    power_factors[(i+self.phase-1) % 3] = (float(meters[f'{alphabetical_index[i]}_pf'])
                                                           if meters.get(f'{alphabetical_index[i]}_pf') else 0)
                power = float(meters['total_act_power']) * self.factor
            # Shelly MiniPM G3
            elif "pm1:0" in status:
                log.debug("single phase shelly")
                powers = [0.0, 0.0, 0.0]
                currents = [0.0, 0.0, 0.0]
                voltages = [0.0, 0.0, 0.0]
                power_factors = [0.0, 0.0, 0.0]
                meters = status['pm1:0']
                powers[self.phase-1] = meters['apower'] * self.factor
                voltages[self.phase-1] = meters['voltage']
                currents[self.phase-1] = meters['current'] * self.factor
                power_factors[self.phase-1] = meters['pf'] if meters.get('pf') else 0
                power = meters['apower'] * self.factor
                frequency = meters['freq']
            elif 'switch:0' in status and 'apower' in status['switch:0']:
                log.debug("single phase shelly")
                powers = [0.0, 0.0, 0.0]
                currents = [0.0, 0.0, 0.0]
                voltages = [0.0, 0.0, 0.0]
                power_factors = [0.0, 0.0, 0.0]
                meters = status['switch:0']
                powers[self.phase-1] = meters['apower'] * self.factor
                voltages[self.phase-1] = meters['voltage']
                currents[self.phase-1] = meters['current'] * self.factor
                # power_factors[self.phase-1] = meters['pf']
                power = meters['apower'] * self.factor
                frequency = meters['freq']
            else:
                log.debug("single phase shelly")
                powers = [0.0, 0.0, 0.0]
                currents = [0.0, 0.0, 0.0]
                voltages = [0.0, 0.0, 0.0]
                power_factors = [0.0, 0.0, 0.0]
                meters = status['em1:0']
                powers[self.phase-1] = meters['act_power']
                voltages[self.phase-1] = meters['voltage']
                currents[self.phase-1] = meters['current'] * self.factor
                power_factors[self.phase-1] = meters['pf']
                power = meters['act_power']  # shelly Pro EM Gen 2
                frequency = meters['freq']

            imported, exported = self.sim_counter.sim_count(power)

            counter_state = CounterState(
                imported=imported,
                exported=exported,
                powers=powers,
                power=power
            )
            if 'frequency' in locals():
                counter_state.frequency = frequency
            if "power_factors" in locals():
                counter_state.power_factors = power_factors
            if "voltages" in locals():
                counter_state.voltages = voltages
            if "currents" in locals():
                counter_state.currents = currents
            self.store.set(counter_state)
        except KeyError:
            log.exception("unsupported shelly device?")


component_descriptor = ComponentDescriptor(configuration_factory=ShellyCounterSetup)
