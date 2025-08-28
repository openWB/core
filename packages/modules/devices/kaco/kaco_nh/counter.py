#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.kaco.kaco_nh.config import KacoNHConfiguration, KacoNHCounterSetup


class KwargsDict(TypedDict):
    device_id: int
    device_config: KacoNHConfiguration


class KacoNHCounter(AbstractCounter):
    def __init__(self, component_config: KacoNHCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.device_config: KacoNHConfiguration = self.kwargs['device_config']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        component_id = self.component_config.configuration.component_id
        response = req.get_http_session().get(
            'http://' + self.device_config.ip_address + ':' + str(self.device_config.port) + '/getdevdata.cgi?device=' +
            str(component_id) + '&sn=' + self.device_config.serial,
            timeout=5).json()
        power = float(response["pac"])
        imported = float(response["iet"]) * 100
        exported = float(response["oet"]) * 100

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KacoNHCounterSetup)
