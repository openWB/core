#!/usr/bin/env python3
"""SunEnergyXT 500 Series – openWB Batteriespeicher-Modul."""
import logging
from typing import Any, Optional

from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sunenergyxt.sunenergyxt.config import SunEnergyXT, SunEnergyXTBatSetup

log = logging.getLogger(__name__)

# Fallback-Limit bis IS vom Gerät gelesen wurde (SunEnergyXT 500, 1 Modul)
_GS_MAX_FALLBACK: int = 800


class SunEnergyXTBat(AbstractBat):
    def __init__(self, component_config: SunEnergyXTBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    def initialize(self) -> None:
        self.device_config: SunEnergyXT = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self._base_url = f"http://{self.device_config.configuration.ip_address}"
        # Wird beim ersten update() aus IS (Max. Inverterleistung) gesetzt.
        # IS berücksichtigt automatisch Modell (500 / 500 Pro) und Anzahl Module (BN).
        self._gs_max: int = _GS_MAX_FALLBACK

    def _read(self) -> dict:
        url = f"{self._base_url}/read"
        return req.get_http_session().get(url, timeout=5).json()

    def _write(self, **kwargs) -> None:
        url = f"{self._base_url}/write"
        payload = {"state": kwargs}
        resp = req.get_http_session().post(url, json=payload, timeout=5)
        log.debug("SunEnergyXT write %s → %s", kwargs, resp.text)

    def update(self) -> None:
        data = self._read()
        reported = data.get("state", {}).get("reported", data)

        soc = int(float(reported.get("SC", 0)))
        power = float(reported.get("PB", 0))

        # IS = max. Inverterleistung: hängt von Modell (500/Pro) und Modulanzahl (BN) ab.
        # Wird als dynamisches GS-Limit verwendet.
        is_value = int(float(reported.get("IS", _GS_MAX_FALLBACK)))
        if is_value > 0:
            self._gs_max = is_value

        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported,
        )
        self.store.set(bat_state)
        log.debug("SunEnergyXT: SoC=%d%%, PB=%.0fW, IS=%dW (gs_max)", soc, power, self._gs_max)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        if power_limit is None:
            log.debug("SunEnergyXT: Automatik (MM=1, GS=0)")
            self._write(MM=1, GS=0)
        elif power_limit == 0:
            log.debug("SunEnergyXT: Entladung gesperrt (MM=0, GS=0)")
            self._write(MM=0, GS=0)
        elif power_limit > 0:
            p = int(min(power_limit, self._gs_max))
            log.debug("SunEnergyXT: Entladen mit %dW (gs_max=%dW)", p, self._gs_max)
            self._write(MM=0, GS=p)
        else:
            p = int(min(abs(power_limit), self._gs_max))
            log.debug("SunEnergyXT: Laden mit %dW (gs_max=%dW)", p, self._gs_max)
            self._write(MM=0, GS=-p)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SunEnergyXTBatSetup)
