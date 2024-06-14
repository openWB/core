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
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.address = address
        self.generation = generation

    def update(self) -> None:
        power = 0
        if self.generation == 1:
            status_url = "http://" + self.address + "/status"
        else:
            status_url = "http://" + self.address + "/rpc/Shelly.GetStatus"
        status = req.get_http_session().get(status_url, timeout=3).json()
        try:
            if self.generation == 1:  # shelly3EM
                meters = status['emeters']
                # shelly3EM has three meters:
                for meter in meters:
                    power = power + meter['power']
                power = power * -1

                voltages = [status['emeters'][0]['voltage'], status['emeters']
                            [1]['voltage'], status['emeters'][2]['voltage']]
                currents = [status['emeters'][0]['current'], status['emeters']
                            [1]['current'], status['emeters'][2]['current']]
                powers = [status['emeters'][0]['power'], status['emeters'][1]['power'], status['emeters'][2]['power']]
                power_factors = [status['emeters'][0]['pf'], status['emeters'][1]['pf'], status['emeters'][2]['pf']]
                imported, exported = self.sim_counter.sim_count(power)
            else:
                # shelly Pro3EM
                voltages = [status['em:0']['a_voltage'], status['em:0']['b_voltage'], status['em:0']['c_voltage']]
                currents = [status['em:0']['a_current'], status['em:0']['b_current'], status['em:0']['c_current']]
                powers = [status['em:0']['a_act_power'], status['em:0']['b_act_power'], status['em:0']['c_act_power']]
                power_factors = [status['em:0']['a_pf'], status['em:0']['b_pf'], status['em:0']['c_pf']]
                power = status['em:0']['total_act_power'] * -1
                imported, exported = self.sim_counter.sim_count(power)

            counter_state = CounterState(
                voltages=voltages,
                currents=currents,
                powers=powers,
                power_factors=power_factors,
                imported=imported,
                exported=exported,
                power=power
            )
            self.store.set(counter_state)
        except KeyError:
            log.exception("unsupported shelly device?")


component_descriptor = ComponentDescriptor(configuration_factory=ShellyCounterSetup)
