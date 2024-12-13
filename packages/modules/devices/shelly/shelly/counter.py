#!/usr/bin/env python3
import logging
from typing import Optional
from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.shelly.config import ShellyCounterSetup

log = logging.getLogger(__name__)


class ShellyCounter(AbstractCounter):

    def __init__(self,
                 device_id: int,
                 component_config: ShellyCounterSetup,
                 address: str,
                 factor: int,
                 generation: Optional[int]) -> None:
        self.component_config = component_config
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.address = address
        self.factor = factor
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
                power = power * self.factor

                voltages = [status['emeters'][i]['voltage'] for i in range(0, 3)]
                currents = [status['emeters'][i]['current'] for i in range(0, 3)]
                powers = [status['emeters'][i]['power'] for i in range(0, 3)]
                power_factors = [status['emeters'][i]['pf'] for i in range(0, 3)]
            else:
                # shelly Pro3EM
                if "em:0" in status:
                    meter = status['em:0']
                    voltages = [meter[f'{i}_voltage'] for i in 'abc']
                    currents = [meter[f'{i}_current'] for i in 'abc']
                    powers = [meter[f'{i}_act_power'] for i in 'abc']
                    power_factors = [meter[f'{i}_pf'] for i in 'abc']
                    power = meter['total_act_power'] * self.factor
                # Shelly MiniPM G3
                else:
                    meter = status['pm1:0']
                    log.debug("single phase shelly")
                    voltages = [meter['voltage'], 0, 0]
                    currents = [meter['current'], 0, 0]
                    power = meter['apower']
                    frequency = meter['freq']

            imported, exported = self.sim_counter.sim_count(power)

            counter_state = CounterState(
                voltages=voltages,
                currents=currents,
                imported=imported,
                exported=exported,
                power=power
            )
            if 'frequency' in locals():
                counter_state.frequency = frequency
            if "power_factors" in locals():
                counter_state.power_factors = power_factors
            if "powers" in locals():
                counter_state.powers = powers
            self.store.set(counter_state)
        except KeyError:
            log.exception("unsupported shelly device?")


component_descriptor = ComponentDescriptor(configuration_factory=ShellyCounterSetup)
