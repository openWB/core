"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden.
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden,
der sonst in das Netz eingespeist werden würde.
"""

from dataclasses import dataclass, field
import logging
from typing import List

from dataclass_utils.factories import currents_list_factory

log = logging.getLogger(__name__)


def get_inverter_default_config():
    return {"max_ac_out": 0}


@dataclass
class Config:
    max_ac_out: float = 0


def config_factory() -> Config:
    return Config()


@dataclass
class Get:
    currents: List[float] = field(default_factory=currents_list_factory)
    daily_exported: float = 0
    monthly_exported: float = 0
    yearly_exported: float = 0
    exported: float = 0
    fault_state: int = 0
    fault_str: str = ""
    power: float = 0


def get_factory() -> Get:
    return Get()


@dataclass
class PvData:
    config: Config = field(default_factory=config_factory)
    get: Get = field(default_factory=get_factory)


class Pv:
    def __init__(self, index):
        self.data = PvData()
        self.num = index
