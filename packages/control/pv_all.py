"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und SmartHome verwendet werden.
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden,
der sonst in das Netz eingespeist werden würde.
"""

from dataclasses import dataclass, field
import logging

from control import data
from helpermodules.constants import NO_ERROR

log = logging.getLogger(__name__)


@dataclass
class Config:
    configured: bool = field(default=False, metadata={"topic": "config/configured"})


def config_factory() -> Config:
    return Config()


@dataclass
class Get:
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str"})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state"})
    monthly_exported: float = field(default=0, metadata={"topic": "get/monthly_exported"})
    yearly_exported: float = field(default=0, metadata={"topic": "get/yearly_exported"})
    exported: float = field(default=0, metadata={"topic": "get/exported"})
    power: float = field(default=0, metadata={"topic": "get/power"})


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
                self.data.get.fault_state = fault_state
                self.data.get.fault_str = NO_ERROR if fault_state == 0 else (
                    "Bitte die Statusmeldungen der Wechselrichter prüfen. "
                    "Es haben nicht alle Module aktuelle Zählerstände geliefert.")
                self.data.get.power = power
                self.data.get.exported = exported
                self.data.config.configured = True
            else:
                self.data.config.configured = False
                # prevent stale PV values when no inverter modules are configured
                self.data.get.power = 0
                self.data.get.exported = 0
                self.data.get.fault_state = 0
                self.data.get.fault_str = NO_ERROR
                self.data.get.daily_exported = 0
                self.data.get.monthly_exported = 0
                self.data.get.yearly_exported = 0
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
