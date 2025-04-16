#!/usr/bin/env python3
import logging
from typing import Optional, Any, TypedDict

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
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
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def __read_json_api_v2(self):
        result = req.get_http_session().get(
            "http://" + self.__device_address + "/api/v2/powermeter",
            timeout=5,
            headers={"Auth-Token": self.__api_v2_token}
        ).json()
        for channel in result:
            if channel["direction"] == "consumption":
                return channel
        raise ValueError("No consumption channel found")

    def __update_json_api_v2(self) -> CounterState:
        # Auslesen einer Sonnenbatterie 8 oder 10 über die integrierte JSON-API v2 des Batteriesystems
        '''
        example data:
        [
            {
                "a_l1": 0,
                "a_l2": 0,
                "a_l3": 0,
                "channel": 1,
                "deviceid": 4,
                "direction": "production",
                "error": -1,
                "kwh_exported": 0,
                "kwh_imported": 0,
                "v_l1_l2": 0,
                "v_l1_n": 0,
                "v_l2_l3": 0,
                "v_l2_n": 0,
                "v_l3_l1": 0,
                "v_l3_n": 0,
                "va_total": 0,
                "var_total": 0,
                "w_l1": 0,
                "w_l2": 0,
                "w_l3": 0,
                "w_total": 0
            },
            {
                "a_l1": 0,
                "a_l2": 0,
                "a_l3": 0,
                "channel": 2,
                "deviceid": 4,
                "direction": "consumption",
                "error": -1,
                "kwh_exported": 0,
                "kwh_imported": 0,
                "v_l1_l2": 0,
                "v_l1_n": 0,
                "v_l2_l3": 0,
                "v_l2_n": 0,
                "v_l3_l1": 0,
                "v_l3_n": 0,
                "va_total": 0,
                "var_total": 0,
                "w_l1": 0,
                "w_l2": 0,
                "w_l3": 0,
                "w_total": 0
            }
        ]
        '''
        counter_state = self.__read_json_api_v2()
        return CounterState(
            power=counter_state["w_total"],
            powers=[counter_state[f"w_l{phase}"] for phase in range(1, 4)],
            currents=[counter_state[f"a_l{phase}"] for phase in range(1, 4)],
            voltages=[counter_state[f"v_l{phase}_n"] for phase in range(1, 4)],
            imported=counter_state["kwh_imported"],
            exported=counter_state["kwh_exported"]
        )

    def update(self) -> None:
        log.debug("Variante: " + str(self.__device_variant))
        if self.__device_variant == 3:
            state = self.__update_json_api_v2()
        elif self.__device_variant in [0, 1, 2]:
            log.debug("Die ausgewählte API bietet keine Verbrauchsdaten!")
        else:
            raise ValueError("Unbekannte API: " + str(self.__device_variant))
        self.store.set(state)


component_descriptor = ComponentDescriptor(configuration_factory=SonnenbatterieConsumptionCounterSetup)
