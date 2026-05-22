#!/usr/bin/env python3
"""SunEnergyXT 500 Series – openWB Batteriespeicher-Modul."""
import logging
from typing import Any, Optional
import requests
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sunenergyxt.sunenergyxt.config import SunEnergyXT, SunEnergyXTBatSetup

log = logging.getLogger(__name__)


class SunEnergyXTBat(AbstractBat):
    def __init__(self, component_config: SunEnergyXTBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    def initialize(self) -> None:
        self.device_config: SunEnergyXT = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self._base_url = (
            f"http://{self.device_config.configuration.ip_address}"
            f":{self.device_config.configuration.port}"
        )
        self._timeout = self.device_config.configuration.timeout

    def _read(self) -> dict:
        url = f"{self._base_url}/read"
        resp = requests.get(url, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    def _write(self, **kwargs) -> None:
        url = f"{self._base_url}/write"
        payload = {"state": kwargs}
        resp = requests.post(url, json=payload, timeout=self._timeout)
        resp.raise_for_status()
        log.debug("SunEnergyXT write %s → %s", kwargs, resp.text)

    def update(self) -> None:
        data = self._read()
        reported = data.get("state", {}).get("reported", data)

        soc = int(float(reported.get("SC", 0)))
        power = float(reported.get("PB", 0))
        max_power = float(reported.get("IS", 0))

        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported,
        )
        bat_state.max_charge_power = max_power
        bat_state.max_discharge_power = max_power
        self.store.set(bat_state)
        log.debug("SunEnergyXT: SoC=%d%%, PB=%.0fW, IS=%.0fW", soc, power, max_power)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        if power_limit is None:
            log.debug("SunEnergyXT: Automatik (MM=1, GS=0)")
            self._write(MM=1, GS=0)
        elif power_limit == 0:
            log.debug("SunEnergyXT: Entladung gesperrt (MM=0, GS=0)")
            self._write(MM=0, GS=0)
        elif power_limit > 0:
            p = int(min(power_limit, 9999))
            log.debug("SunEnergyXT: Entladen mit %dW", p)
            self._write(MM=0, GS=p)
        else:
            p = int(min(abs(power_limit), 9999))
            log.debug("SunEnergyXT: Laden mit %dW", p)
            self._write(MM=0, GS=-p)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SunEnergyXTBatSetup)
