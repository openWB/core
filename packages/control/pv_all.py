"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden.
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden,
der sonst in das Netz eingespeist werden würde.
"""

from dataclasses import asdict, dataclass, field
import logging

from control import data
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


@dataclass
class Config:
    configured: bool = False


def config_factory() -> Config:
    return Config()


@dataclass
class Get:
    daily_exported: float = 0
    monthly_exported: float = 0
    yearly_exported: float = 0
    exported: float = 0
    power: float = 0


def get_factory() -> Get:
    return Get()


@dataclass
class PvAllData:
    config: Config = field(default_factory=config_factory)
    get: Get = field(default_factory=get_factory)


class PvAll:
    """
    """

    def __init__(self):
        self.data = PvAllData()

    def calc_power_for_all_components(self) -> None:
        try:
            if len(data.data.pv_data) >= 1:
                # Summe von allen konfigurierten Modulen
                self.data.get.exported = 0
                self.data.get.daily_exported = 0
                self.data.get.monthly_exported = 0
                self.data.get.yearly_exported = 0
                self.data.get.power = 0
                for module in data.data.pv_data:
                    try:
                        if "pv" in module:
                            module_data = data.data.pv_data[module].data
                            self.data.get.power += module_data.get.power
                            self.data.get.exported += module_data.get.exported
                            self.data.get.daily_exported += module_data.get.daily_exported
                            self.data.get.monthly_exported += module_data.get.monthly_exported
                            self.data.get.yearly_exported += module_data.get.yearly_exported
                    except Exception:
                        log.exception("Fehler im allgemeinen PV-Modul für "+str(module))
                # Alle Summentopics im Dict publishen
                {Pub().pub("openWB/set/pv/get/"+k, v) for (k, v) in asdict(self.data.get).items()}
                self.data.config.configured = True
                Pub().pub("openWB/set/pv/config/configured", self.data.config.configured)
            else:
                self.data.config.configured = False
                Pub().pub("openWB/set/pv/config/configured", self.data.config.configured)
                {Pub().pub("openWB/pv/get/"+k, 0) for (k, _) in asdict(self.data.get).items()}
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
