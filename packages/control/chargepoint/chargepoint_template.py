from dataclasses import asdict, dataclass, field
import logging
import traceback
from typing import Dict, List

from control import data
from control import ev as ev_module
from dataclass_utils.factories import empty_dict_factory, empty_list_factory
from helpermodules.abstract_plans import AutolockPlan
from helpermodules import timecheck


log = logging.getLogger(__name__)


def get_chargepoint_template_default():
    default = asdict(CpTemplateData())
    default["autolock"].pop("plans")
    return default


def get_autolock_plan_default():
    return asdict(AutolockPlan())


@dataclass
class Autolock:
    active: bool = False
    plans: Dict[int, AutolockPlan] = field(default_factory=empty_dict_factory)
    wait_for_charging_end: bool = False


def autolock_factory():
    return Autolock()


@dataclass
class CpTemplateData:
    autolock: Autolock = field(default_factory=autolock_factory)
    id: int = 0
    max_current_multi_phases: int = 32
    max_current_single_phase: int = 32
    name: str = "Standard Ladepunkt-Vorlage"
    rfid_enabling: bool = False
    valid_tags: List = field(default_factory=empty_list_factory)


class CpTemplate:
    """ Vorlage für einen Ladepunkt.
    """

    def __init__(self):
        self.data: CpTemplateData = CpTemplateData()

    def is_locked_by_autolock(self, charge_state: bool) -> bool:
        if self.data.autolock.active:
            if self.data.autolock.plans:
                if timecheck.check_plans_timeframe(self.data.autolock.plans) is not None:
                    if self.data.autolock.wait_for_charging_end:
                        return False if charge_state else True
                    else:
                        return True
                else:
                    return False
            else:
                log.info("Keine Sperrung durch Autolock, weil keine Zeitpläne konfiguriert sind.")
                return False
        else:
            return False

    def get_ev(self, rfid, assigned_ev):
        """ermittelt das dem Ladepunkt zugeordnete EV

        Parameter
        ---------
        rfid: str
            Tag, der einem EV zugeordnet werden soll.
        assigned_ev: int
            dem Ladepunkt fest zugeordnetes EV
        Return
        ------
        num: int
            Nummer des zugeordneten EVs, -1 wenn keins zugeordnet werden konnte.
        message: str
            Status-Text
        """
        num = -1
        message = None
        try:
            if data.data.optional_data.data.rfid.active and rfid is not None:
                vehicle = ev_module.get_ev_to_rfid(rfid)
                if vehicle is None:
                    num = -1
                    message = "Keine Ladung, da dem RFID-Tag " + str(rfid)+" kein EV-Profil zugeordnet werden kann."
                else:
                    num = vehicle
            else:
                num = assigned_ev

            return num, message
        except Exception:
            log.exception(
                "Fehler in der Ladepunkt-Template Klasse")
            return num, "Keine Ladung, da ein interner Fehler aufgetreten ist: " + traceback.format_exc()
