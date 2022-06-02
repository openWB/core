#!/usr/bin/env python3
from dataclasses import dataclass
import logging
from typing import Dict
from requests import HTTPError

from modules.common.abstract_component import AbstractConfiguration, AbstractSetup, from_dict
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_counter_value_store
from modules.tesla.http_client import PowerwallHttpClient

log = logging.getLogger(__name__)


@dataclass
class Configuration(AbstractConfiguration):
    pass


@dataclass
class Setup(AbstractSetup):
    name: str = "Tesla Zähler"
    type: str = "counter"
    id: int = 0
    configuration: Configuration = Configuration()


class TeslaCounter:
    def __init__(self, component_config: Dict) -> None:
        self.component_config = component_config if isinstance(
            component_config, Setup) else from_dict(component_config, Setup)
        self.__store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: PowerwallHttpClient, aggregate):
        # read firmware version
        status = client.get_json("/api/status")
        log.debug('Firmware: ' + status["version"])
        try:
            # read additional info if firmware supports
            meters_site = client.get_json("/api/meters/site")
            powerwall_state = CounterState(
                imported=aggregate["site"]["energy_imported"],
                exported=aggregate["site"]["energy_exported"],
                power=aggregate["site"]["instant_power"],
                voltages=[meters_site[0]["Cached_readings"]["v_l" + str(phase) + "n"] for phase in range(1, 4)],
                currents=[meters_site[0]["Cached_readings"]["i_" + phase + "_current"] for phase in ["a", "b", "c"]],
                powers=[meters_site[0]["Cached_readings"]["real_power_" + phase] for phase in ["a", "b", "c"]]
            )
        except (KeyError, HTTPError):
            log.debug(
                "Firmware seems not to provide detailed phase measurements. Fallback to total power only.")
            powerwall_state = CounterState(
                imported=aggregate["site"]["energy_imported"],
                exported=aggregate["site"]["energy_exported"],
                power=aggregate["site"]["instant_power"]
            )
        self.__store.set(powerwall_state)
