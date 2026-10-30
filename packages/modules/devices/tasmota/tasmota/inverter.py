#!/usr/bin/env python3
from typing import Any, TypedDict
import logging

from modules.devices.tasmota.tasmota.config import TasmotaInverterSetup
from modules.common.abstract_device import AbstractInverter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount import SimCounter
from modules.common import req
from modules.common.component_state import InverterState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from modules.devices.tasmota.tasmota.parser import TasmotaParser

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
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.__phase: int = self.kwargs['phase']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)

    def update(self):
        url = "http://" + self.__ip_address + "/cm?cmnd=Status%208"
        response = req.get_http_session().get(url, timeout=5).json()

        data = TasmotaParser(response, self.__phase)
        power = data.power * -1
        exported = data.exported
        if data.meter_type == 'ENERGY':
            self.peak_filter.check_values(power)
            _, exported = self.sim_counter.sim_count(power)
        else:
            _, exported = self.peak_filter.check_values(power, None, exported)

        inverter_state = InverterState(
            power=power,
            exported=exported,
            currents=data.currents
        )

        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=TasmotaInverterSetup)
