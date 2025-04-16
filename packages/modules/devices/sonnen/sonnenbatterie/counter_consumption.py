#!/usr/bin/env python3
import logging
from typing import Any, TypedDict, Optional

from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store

from modules.devices.sonnen.sonnenbatterie.api import JsonApi, JsonApiVersion
from modules.devices.sonnen.sonnenbatterie.config import SonnenbatterieConsumptionCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_address: str
    device_variant: int
    api_v2_token: Optional[str]


class SonnenbatterieConsumptionCounter(AbstractCounter):
    def __init__(self, component_config: SonnenbatterieConsumptionCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_address: str = self.kwargs['device_address']
        self.__device_variant: int = self.kwargs['device_variant']
        self.__api_v2_token: Optional[str] = self.kwargs['device_api_v2_token']
        if self.__device_variant in [0, 1, 2]:
            raise ValueError("Die ausgewählte API bietet keine Verbrauchsdaten!")
        if self.__device_variant != 3:
            raise ValueError("Unbekannte API: " + str(self.__device_variant))

        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.api = JsonApi(host=self.__device_address,
                           api_version=JsonApiVersion.V2,
                           auth_token=self.__api_v2_token)

    def update(self) -> None:
        self.store.set(self.api.update_consumption_counter())


component_descriptor = ComponentDescriptor(configuration_factory=SonnenbatterieConsumptionCounterSetup)
