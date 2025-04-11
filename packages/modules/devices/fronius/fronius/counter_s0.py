#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.fronius.fronius.config import FroniusConfiguration, FroniusS0CounterSetup


class KwargsDict(TypedDict):
    device_id: int
    device_config: FroniusConfiguration


class FroniusS0Counter(AbstractCounter):
    def __init__(self, component_config: FroniusS0CounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.device_config: FroniusConfiguration = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        session = req.get_http_session()
        response = session.get(
            'http://'+self.device_config.ip_address+'/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
            timeout=5)
        # Wenn WR aus bzw. im Standby (keine Antwort), ersetze leeren Wert durch eine 0.
        power = float(response.json()["Body"]["Data"]["Site"]["P_Grid"]) or 0

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FroniusS0CounterSetup)
