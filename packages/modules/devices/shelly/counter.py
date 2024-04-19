#!/usr/bin/env python3
import logging
from typing import Optional
from modules.common import req
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.config import ShellyCounterSetup

log = logging.getLogger(__name__)


class ShellyCounter:

    def __init__(self,
                 device_id: int,
                 component_config: ShellyCounterSetup,
                 address: str,
                 generation: Optional[int]) -> None:
        self.component_config = component_config
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.address = address
        self.generation = generation

    def update(self) -> None:
        status_url = "http://" + self.address + "/rpc/Shelly.GetStatus"
        status = req.get_http_session().get(status_url, timeout=3).json()
        try:
            if 'em:0' in status:  # 3 phased energy meter gen2 and above
                voltages = [status['em:0']['a_voltage'], status['em:0']['b_voltage'], status['em:0']['c_voltage']]
                currents = [status['em:0']['a_current'], status['em:0']['b_current'], status['em:0']['c_current']]
                powers = [status['em:0']['a_act_power'], status['em:0']['b_act_power'], status['em:0']['c_act_power']]
                power_factors = [status['em:0']['a_pf'], status['em:0']['b_pf'], status['em:0']['c_pf']]
                power = status['em:0']['total_act_power'] * -1
                frequency = status['em:0']['a_freq']  # status['em:0']['b_freq'], status['em:0']['c_freq']
                imported, exported = self.sim_counter.sim_count(power)

                counter_state = CounterState(
                    voltages=voltages,
                    currents=currents,
                    powers=powers,
                    power_factors=power_factors,
                    imported=imported,
                    exported=exported,
                    power=power,
                    frequency=frequency
                )
                self.store.set(counter_state)
        except KeyError:
            log.exception("unsupported shelly device?")


component_descriptor = ComponentDescriptor(configuration_factory=ShellyCounterSetup)
