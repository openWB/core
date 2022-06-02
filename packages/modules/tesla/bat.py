#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Dict

from modules.common.abstract_component import AbstractConfiguration, AbstractSetup, from_dict
from modules.common.component_state import BatState
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_bat_value_store
from modules.tesla.http_client import PowerwallHttpClient


@dataclass
class Configuration(AbstractConfiguration):
    pass


@dataclass
class Setup(AbstractSetup):
    name: str = "Tesla Speicher"
    type: str = "bat"
    id: int = 0
    configuration: Configuration = Configuration()


class TeslaBat:
    def __init__(self, component_config: Dict) -> None:
        self.component_config = component_config if isinstance(
            component_config, Setup) else from_dict(component_config, Setup)
        self.__store = get_bat_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: PowerwallHttpClient, aggregate) -> None:
        self.__store.set(BatState(
            imported=aggregate["battery"]["energy_imported"],
            exported=aggregate["battery"]["energy_exported"],
            power=-aggregate["battery"]["instant_power"],
            soc=client.get_json("/api/system_status/soe")["percentage"]
        ))
