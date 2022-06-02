#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Dict

from modules.common.abstract_component import AbstractConfiguration, AbstractSetup, from_dict
from modules.common.component_state import InverterState
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_inverter_value_store
from modules.tesla.http_client import PowerwallHttpClient


@dataclass
class Configuration(AbstractConfiguration):
    pass


@dataclass
class Setup(AbstractSetup):
    name: str = "Tesla Wechselrichter"
    type: str = "inverter"
    id: int = 0
    configuration: Configuration = Configuration()


class TeslaInverter:
    def __init__(self, component_config: Dict) -> None:
        self.component_config = component_config if isinstance(
            component_config, Setup) else from_dict(component_config, Setup)
        self.__store = get_inverter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: PowerwallHttpClient, aggregate) -> None:
        pv_watt = aggregate["solar"]["instant_power"]
        if pv_watt > 5:
            pv_watt = pv_watt*-1
        self.__store.set(InverterState(
            counter=aggregate["solar"]["energy_exported"],
            power=pv_watt
        ))
