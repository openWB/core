from dataclasses import dataclass, field
import logging

from control import data
from control.chargepoint.chargepoint_state import ChargepointState
from helpermodules.constants import NO_ERROR


log = logging.getLogger(__name__)


@dataclass
class AllGet:
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
    power: float = field(default=0, metadata={"topic": "get/power"})
    imported: float = field(default=0, metadata={"topic": "get/imported"})
    exported: float = field(default=0, metadata={"topic": "get/exported"})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state"})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str"})


def all_get_factory() -> AllGet:
    return AllGet()


@dataclass
class AllChargepointData:
    get: AllGet = field(default_factory=all_get_factory)


def all_chargepoint_data_factory() -> AllChargepointData:
    return AllChargepointData()


@dataclass
class AllChargepoints:
    data: AllChargepointData = field(default_factory=all_chargepoint_data_factory)

    def get_cp_sum(self):
        """ ermittelt die aktuelle Leistung und Zählerstand von allen Ladepunkten.
        """
        imported, exported, power = 0, 0, 0
        try:
            fault_state = 0
            for cp in data.data.cp_data.values():
                imported = imported + cp.data.get.imported
                exported = exported + cp.data.get.exported
                try:
                    power = power + cp.data.get.power
                except Exception:
                    log.exception(f"Fehler in der allgemeinen Ladepunkt-Klasse für Ladepunkt {cp.num}")
                fault_state = max(fault_state, cp.data.get.fault_state)
            # Ladepunkte setzen ihre Werte im Fehlerfall selbst zurück
            self.data.get.power = power
            self.data.get.imported = imported
            self.data.get.exported = exported
            self.data.get.fault_state = fault_state
            self.data.get.fault_str = NO_ERROR if fault_state == 0 else (
                "Bitte die Statusmeldungen der Ladepunkte prüfen. "
                "Es haben nicht alle Ladepunkte aktuelle Zählerstände geliefert.")
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")
