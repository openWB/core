#!/usr/bin/env python3
from typing import Any, TypedDict
import logging

from modules.devices.tasmota.tasmota.config import TasmotaCounterSetup
from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.common.simcount import SimCounter
from modules.common import req
from modules.common.component_state import CounterState

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str
    phase: int


class TasmotaCounter(AbstractCounter):
    def __init__(self, component_config: TasmotaCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.__phase: int = self.kwargs['phase']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        url = "http://" + self.__ip_address + "/cm?cmnd=Status%208"
        response = req.get_http_session().get(url, timeout=5).json()

        if 'ENERGY' in response['StatusSNS']:
            voltages = [0.0, 0.0, 0.0]
            powers = [0.0, 0.0, 0.0]
            currents = [0.0, 0.0, 0.0]
            power_factors = [0.0, 0.0, 0.0]

            power = float(response['StatusSNS']['ENERGY']['Power'])
            voltages[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Voltage'])
            powers[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Power'])
            currents[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Current'])
            power_factors[self.__phase-1] = float(response['StatusSNS']['ENERGY']['Factor'])
            imported = float(response['StatusSNS']['ENERGY']['Total']*1000)
            _, exported = self.sim_counter.sim_count(power)
        elif 'Itron' in response['StatusSNS']:
            power = float(response['StatusSNS']['Itron']['Power'])
            imported = float(response['StatusSNS']['Itron']['E_in']*1000)
            exported = float(response['StatusSNS']['Itron']['E_out']*1000)
        elif 'MT681' in response['StatusSNS']:
            power = float(response['StatusSNS']['MT681']['Watt_summe'])
            imported = float(response['StatusSNS']['MT681']['Total_in']*1000)
            exported = float(response['StatusSNS']['MT681']['Total_out']*1000)
        else:
            raise ValueError("Nicht unterstützter Tasmota Zählertyp. Bitte an den Support wenden.")

        counter_state = CounterState(
            power=power,
            imported=imported,
            exported=exported
        )
        if 'voltages' in locals():
            counter_state.voltages = voltages
        if 'currents' in locals():
            counter_state.currents = currents
        if 'powers' in locals():
            counter_state.powers = powers
        if 'power_factors' in locals():
            counter_state.power_factors = power_factors

        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaCounterSetup)
