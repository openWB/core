#!/usr/bin/env python3
import logging
from typing import Any, TypedDict, Optional

from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store

from modules.devices.sonnen.sonnenbatterie.api import JsonApi, RestApi2, JsonApiVersion
from modules.devices.sonnen.sonnenbatterie.config import SonnenbatterieCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    api_v2_token: str
    device_id: int
    device_address: str
    device_variant: int


class SonnenbatterieCounter(AbstractCounter):
    def __init__(self, component_config: SonnenbatterieCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__device_address: str = self.kwargs['device_address']
        self.__device_variant: int = self.kwargs['device_variant']
        self.__api_v2_token: Optional[str] = self.kwargs['device_api_v2_token']
        if self.__device_variant == 0:
            raise ValueError("Die API 'Rest-API 1' bietet keine EVU Daten!")
        if self.__device_variant not in [1, 2, 3]:
            raise ValueError("Unbekannte API: " + str(self.__device_variant))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        if self.__device_variant == 2:
            self.api = RestApi2(host=self.__device_address)
        else:
            self.api = JsonApi(host=self.__device_address,
                               api_version=JsonApiVersion.V2 if self.__device_variant == 3 else JsonApiVersion.V1,
                               auth_token=self.__api_v2_token if self.__device_variant == 3 else None)

    def update(self) -> None:
        self.store.set(self.api.update_grid_counter(sim_counter=self.sim_counter))


component_descriptor = ComponentDescriptor(configuration_factory=SonnenbatterieCounterSetup)
