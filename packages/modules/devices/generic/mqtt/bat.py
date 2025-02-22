#!/usr/bin/env python3
from typing import Dict, Optional, Union
from helpermodules.pub import Pub
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.fault_state import ComponentInfo, FaultState

from dataclass_utils import dataclass_from_dict
from modules.common.component_type import ComponentDescriptor
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._battery import get_bat_value_store
from modules.devices.generic.mqtt.config import MqttBatSetup


class MqttBat(AbstractBat):
    def __init__(self, component_config: Union[Dict, MqttBatSetup], device_id: int) -> None:
        self.component_config = dataclass_from_dict(MqttBatSetup, component_config)
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="pv")
        self.fault_state = FaultState(ComponentInfo.from_component_config(component_config))
        self.store = get_bat_value_store(self.component_config.id)

    def update(self, received_topics: Dict) -> None:
        power = received_topics.get(f"openWB/mqtt/bat/{self.component_config.id}/get/power")
        soc = received_topics.get(f"openWB/mqtt/bat/{self.component_config.id}/get/soc")
        if (received_topics.get(f"openWB/mqtt/bat/{self.component_config.id}/get/imported") and
                received_topics.get(f"openWB/mqtt/bat/{self.component_config.id}/get/exported")):
            imported = received_topics.get(f"openWB/mqtt/bat/{self.component_config.id}/get/imported")
            exported = received_topics.get(f"openWB/mqtt/bat/{self.component_config.id}/get/exported")
        else:
            imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        Pub().pub(f"openWB/mqtt/bat/{self.component_config.id}/set/powerLimit", power_limit)


component_descriptor = ComponentDescriptor(configuration_factory=MqttBatSetup)
