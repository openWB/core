#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.kaco.kaco_nh.config import KacoNHBatSetup
from modules.devices.kaco.kaco_nh.config import KacoNHConfiguration


class KwargsDict(TypedDict):
    device_config: KacoNHConfiguration


class KacoNHBat(AbstractBat):
    def __init__(self, component_config: KacoNHBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: KacoNHConfiguration = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        response = req.get_http_session().get(
            'http://' + self.device_config.ip_address + ':' + str(self.device_config.port) + '/getdevdata.cgi?device=' +
            str(self.component_config.configuration.id) + '&sn=' + self.device_config.serial_number,
            timeout=5).json()
        power = int(response["pb"]) * -1
        soc = float(response["soc"])

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=KacoNHBatSetup)
