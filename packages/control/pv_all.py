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
                for module in data.data.pv_data.values():
                    try:
                        power += module.data.get.power
                    except Exception:
                        log.exception(f"Fehler im allgemeinen PV-Modul für pv{module.num}")
                    exported += module.data.get.exported
                    fault_state = max(fault_state, module.data.get.fault_state)
                    limit = data.data.io_actions.stepwise_control(module.num)[1]
                    if module.data.get.fault_state == 0 and limit.message is not None:
                        # Fehlermeldung nicht überschreiben
                        module.data.get.fault_str = limit.message
                        Pub().pub(f"openWB/set/pv/{module.num}/get/fault_str", limit.message)
                self.data.get.fault_state = fault_state
                self.data.get.fault_str = NO_ERROR if fault_state == 0 else (
                    "Bitte die Statusmeldungen der Wechselrichter prüfen. "
                    "Es haben nicht alle Module aktuelle Zählerstände geliefert.")
                self.data.get.power = power
                Pub().pub("openWB/set/pv/get/power", self.data.get.power)
                self.data.get.exported = exported
                Pub().pub("openWB/set/pv/get/exported", self.data.get.exported)
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
