#!/usr/bin/env python3
import logging
from typing import Optional, TypedDict, Any
from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_bat_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.shelly.shelly.config import ShellyBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    factor: int
    generation: Optional[int]


class ShellyBat(AbstractBat):
    def __init__(self, component_config: ShellyBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.address: str = self.kwargs['ip_address']
        self.factor: int = self.kwargs['factor']
        self.generation: Optional[int] = self.kwargs['generation']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        power = 0
        if self.generation == 1:
            status_url = "http://" + self.address + "/status"
        else:
            status_url = "http://" + self.address + "/rpc/Shelly.GetStatus"
        status = req.get_http_session().get(status_url, timeout=3).json()

        try:
            if self.generation == 1:
                if 'meters' in status:
                    meters = status['meters']  # shelly
                else:
                    meters = status['emeters']  # shellyEM & shelly3EM
                # shellyEM has one meter, shelly3EM has three meters:
                for meter in meters:
                    power = power + meter['power']
                currents = [0, 0, 0]
            else:
                if 'switch:0' in status and 'apower' in status['switch:0']:
                    power = status['switch:0']['apower']
                    currents = [status['switch:0']['current'], 0, 0]
                elif 'em1:0' in status:
                    power = status['em1:0']['act_power']  # shelly Pro EM Gen 2
                    currents = [status['em1:0']['current'], 0, 0]
                elif 'pm1:0' in status:
                    power = status['pm1:0']['apower']  # shelly PM Mini Gen 3
                    currents = [status['pm1:0']['current'], 0, 0]
                else:
                    power = status['em:0']['total_act_power']  # shelly Pro3EM
                    currents = [meter[f'{i}_current'] for i in 'abc']

            power = power * self.factor
            imported, exported = self.sim_counter.sim_count(power)
            bat_state = BatState(
                power=power,
                imported=imported,
                exported=exported,
                currents=currents
            )
            self.store.set(bat_state)
        except KeyError:
            log.exception("unsupported shelly device.")


component_descriptor = ComponentDescriptor(configuration_factory=ShellyBatSetup)
