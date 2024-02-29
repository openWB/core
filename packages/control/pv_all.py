"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und SmartHome verwendet werden.
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden,
der sonst in das Netz eingespeist werden würde.
"""

from dataclasses import asdict, dataclass, field
import logging

from control import data
from helpermodules.constants import NO_ERROR
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
    fault_str: str = NO_ERROR
    fault_state: int = 0
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
                exported = 0
                power = 0
                fault_state = 0
                for module in data.data.pv_data:
                    try:
                        if "pv" in module:
                            module_data = data.data.pv_data[module].data
                            if module_data.get.fault_state < 2:
                                power += module_data.get.power
                                exported += module_data.get.exported
                            else:
                                if fault_state < module_data.get.fault_state:
                                    fault_state = module_data.get.fault_state
                    except Exception:
                        log.exception("Fehler im allgemeinen PV-Modul für "+str(module))
                if fault_state == 0:
                    self.data.get.exported = exported
                    Pub().pub("openWB/set/pv/get/exported", self.data.get.exported)
                    self.data.get.fault_state = 0
                    self.data.get.fault_str = NO_ERROR
                else:
                    self.data.get.fault_state = fault_state
                    self.data.get.fault_str = "Bitte die Statusmeldungen der Wechselrichter prüfen."
                self.data.get.power = power
                Pub().pub("openWB/set/pv/get/power", self.data.get.power)
                Pub().pub("openWB/set/pv/get/fault_state", self.data.get.fault_state)
                Pub().pub("openWB/set/pv/get/fault_str", self.data.get.fault_str)
                self.data.config.configured = True
                Pub().pub("openWB/set/pv/config/configured", self.data.config.configured)
            else:
                self.data.config.configured = False
                Pub().pub("openWB/set/pv/config/configured", self.data.config.configured)
                {Pub().pub("openWB/pv/get/"+k, 0) for (k, _) in asdict(self.data.get).items()}
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
