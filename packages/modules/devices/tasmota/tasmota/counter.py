#!/usr/bin/env python3
from typing import Any, TypedDict
import logging

from modules.devices.tasmota.tasmota.config import TasmotaCounterSetup
from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount import SimCounter
from modules.common import req
from modules.common.component_state import CounterState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from modules.devices.tasmota.tasmota.parser import TasmotaParser

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
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.__phase: int = self.kwargs['phase']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self):
        url = "http://" + self.__ip_address + "/cm?cmnd=Status%208"
        response = req.get_http_session().get(url, timeout=5).json()

        data = TasmotaParser(response, self.__phase)
        power = data.power
        measured_exported = None if data.meter_type == 'ENERGY' else data.exported
        imported, exported = self.peak_filter.check_values(power, data.imported, measured_exported)
        if data.meter_type == 'ENERGY':
            _, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            power=power,
            imported=imported,
            exported=exported,
            voltages=data.voltages,
            currents=data.currents,
            powers=data.powers,
            power_factors=data.power_factors
        )

        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaCounterSetup)
