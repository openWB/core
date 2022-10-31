""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.

In den control Parametern wird sich der Lademodus, Submodus, Priorität, Phasen und Stromstärke gemerkt,
mit denen das EV aktuell in der Regelung berücksichtigt wird. Bei der Ermittlung der benötigten Strom-
stärke wird auch geprüft, ob sich an diesen Parametern etwas geändert hat. Falls ja, muss das EV
in der Regelung neu priorisiert werden und eine neue Zuteilung des Stroms erhalten.
"""
from dataclasses import asdict, dataclass, field
import logging
import traceback
from typing import List, Dict, Optional, Tuple

from control import data
from helpermodules.abstract_plans import ScheduledChargingPlan, TimeChargingPlan
from helpermodules.pub import Pub
from helpermodules import timecheck
from modules.common.abstract_soc import AbstractSoc

log = logging.getLogger(__name__)


def get_vehicle_default() -> dict:
    return {
        "charge_template": 0,
        "ev_template": 0,
        "name": "Standard-Fahrzeug",
        "tag_id": [],
        "get/soc": 0
    }


def get_charge_template_default() -> dict:
    ct_default = asdict(ChargeTemplateData())
    ct_default["chargemode"]["scheduled_charging"].pop("plans")
    ct_default["time_charging"].pop("plans")
    return ct_default

# Avoid anti-pattern: mtuable default arguments


def emtpy_list_factory():
    return []


def empty_dict_factory() -> Dict:
    return {}


@dataclass
class ScheduledCharging:
    plans: Dict[int, ScheduledChargingPlan] = field(default_factory=empty_dict_factory)


@dataclass
class TimeCharging:
    active: bool = False
    plans: Dict[int, TimeChargingPlan] = field(default_factory=empty_dict_factory)


@dataclass
class Limit:
    selected: str = "none"
    amount: int = 1000
    soc: int = 50


def limit_factory() -> Limit:
    return Limit()


@dataclass
class InstantCharging:
    current: int = 10
    limit: Limit = field(default_factory=limit_factory)


@dataclass
class PvCharging:
    min_soc_current: int = 10
    min_current: int = 0
    feed_in_limit: bool = False
    min_soc: int = 0
    max_soc: int = 100


def pv_charging_factory() -> PvCharging:
    return PvCharging()


def scheduled_charging_factory() -> ScheduledCharging:
    return ScheduledCharging()


def instant_charging_factory() -> InstantCharging:
    return InstantCharging()


@dataclass
class Chargemode:
    selected: str = "stop"
    pv_charging: PvCharging = field(default_factory=pv_charging_factory)
    scheduled_charging: ScheduledCharging = field(default_factory=scheduled_charging_factory)
    instant_charging: InstantCharging = field(default_factory=instant_charging_factory)


def time_charging_factory() -> TimeCharging:
    return TimeCharging()


def chargemode_factory() -> Chargemode:
    return Chargemode()


@dataclass
class ChargeTemplateData:
    name: str = "Standard-Ladeprofil-Vorlage"
    disable_after_unplug: bool = False
    prio: bool = False
    load_default: bool = False
    time_charging: TimeCharging = field(default_factory=time_charging_factory)
    chargemode: Chargemode = field(default_factory=chargemode_factory)


@dataclass
class Soc:
    request_interval_charging: int = 5
    request_interval_not_charging: int = 720
    request_only_plugged: bool = False


def soc_factory() -> Soc:
    return Soc()


@dataclass
class EvTemplateData:
    name: str = "Standard-Fahrzeug-Vorlage"
    max_current_multi_phases: int = 16
    max_phases: int = 3
    phase_switch_pause: int = 2
    prevent_phase_switch: bool = False
    prevent_charge_stop: bool = False
    control_pilot_interruption: bool = False
    control_pilot_interruption_duration: int = 4
    average_consump: float = 17
    min_current: int = 6
    max_current_one_phase: int = 32
    battery_capacity: float = 82
    nominal_difference: int = 2
    soc: Soc = field(default_factory=soc_factory)


def ev_template_data_factory() -> EvTemplateData:
    return EvTemplateData()


@dataclass
class ControlParameter:
    required_current: float = 0
    phases: int = 0
    prio: bool = False
    timestamp_switch_on_off: Optional[str] = None
    timestamp_auto_phase_switch: Optional[str] = None
    timestamp_perform_phase_switch: Optional[str] = None
    submode: str = "stop"
    chargemode: str = "stop"
    used_amount_instant_charging: float = 0
    imported_at_plan_start: float = 0
    current_plan: Optional[str] = None


@dataclass
class EvTemplate:
    """ Klasse mit den EV-Daten
    """

    data: EvTemplateData = field(default_factory=ev_template_data_factory)
    et_num: int = 0

    def soc_interval_expired(
            self, plug_state: bool, charge_state: bool, soc_timestamp: str) -> bool:
        request_soc = False
        if soc_timestamp == "":
            # Initiale Abfrage
            request_soc = True
        else:
            if (self.data.soc.request_only_plugged is False or
                    (self.data.soc.request_only_plugged is True and plug_state is True)):
                if charge_state is True:
                    interval = self.data.soc.request_interval_charging
                else:
                    interval = self.data.soc.request_interval_not_charging
                # Zeitstempel prüfen, ob wieder abgefragt werden muss.
                if timecheck.check_timestamp(soc_timestamp, interval*60-5) is False:
                    # Zeit ist abgelaufen
                    request_soc = True
        return request_soc


def ev_template_factory() -> EvTemplate:
    return EvTemplate()


@dataclass
class Set:
    ev_template: EvTemplate = field(default_factory=ev_template_factory)


def set_factory() -> Set:
    return Set()


@dataclass
class Get:
    soc: int = 0
    soc_timestamp: str = ""
    force_soc_update: bool = False
    range: float = 0


def control_parameter_factory() -> ControlParameter:
    return ControlParameter()


def get_factory() -> Get:
    return Get()


@dataclass
class EvData:
    set: Set = field(default_factory=set_factory)
    control_parameter: ControlParameter = field(default_factory=control_parameter_factory)
    charge_template: int = 0
    ev_template: int = 0
    name: str = "Standard-Fahrzeug"
    tag_id: List[str] = field(default_factory=emtpy_list_factory)
    get: Get = field(default_factory=get_factory)


class Ev:
    """Logik des EV
    """

    def __init__(self, index: int):
        try:
            self.ev_template: EvTemplate = EvTemplate()
            self.charge_template: ChargeTemplate = ChargeTemplate(0)
            self.soc_module: AbstractSoc = None
            self.num = index
            self.data = EvData()
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))

    def reset_ev(self):
        """ setzt alle Werte zurück, die während des Algorithmus gesetzt werden.
        """
        try:
            log.debug("EV "+str(self.num)+" zurückgesetzt.")
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/required_current", 0)
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/timestamp_auto_phase_switch", None)
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/timestamp_perform_phase_switch", None)
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/submode", "stop")
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/chargemode", "stop")
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/used_amount_instant_charging", 0)
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/imported_at_plan_start", 0)
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/current_plan", None)
            self.data.control_parameter.required_current = 0
            self.data.control_parameter.timestamp_auto_phase_switch = None
            self.data.control_parameter.timestamp_perform_phase_switch = None
            self.data.control_parameter.submode = "stop"
            self.data.control_parameter.chargemode = "stop"
            self.data.control_parameter.used_amount_instant_charging = 0
            self.data.control_parameter.imported_at_plan_start = 0
            self.data.control_parameter.current_plan = None
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))

    def get_required_current(self,
                             charged_since_mode_switch: float,
                             max_phases: int,
                             phase_switch_supported: bool) -> Tuple[bool, Optional[str], str, float, int]:
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)

        Parameter
        ---------
        imported_since_mode_switch: float
            seit dem letzten Lademodi-Wechsel geladene Energie.
        Return
        ------
        state: bool
            Soll geladen werden?
        message: str
            Nachricht, warum nicht geladen werden soll
        submode: str
            Lademodus, in dem tatsächlich geladen wird
        required_current: int
            Strom, der nach Ladekonfiguration benötigt wird
        """
        phases = None
        required_current = None
        message = None
        state = True
        try:
            if self.charge_template.data.chargemode.selected == "scheduled_charging":
                used_amount = charged_since_mode_switch - self.data.control_parameter.imported_at_plan_start
                plan_data = self.charge_template.scheduled_charging_recent_plan(
                    self.data.get.soc,
                    self.ev_template,
                    self.data.control_parameter.phases,
                    used_amount,
                    max_phases,
                    phase_switch_supported)
                if plan_data:
                    name = self.charge_template.data.chargemode.scheduled_charging.plans[plan_data.num].name
                    # Wenn mit einem neuen Plan geladen wird, muss auch die Energiemenge von neuem gezählt werden.
                    if (self.charge_template.data.chargemode.scheduled_charging.plans[plan_data.num].limit.
                            selected == "amount" and
                            name != self.data.control_parameter.current_plan):
                        self.data.control_parameter.imported_at_plan_start = charged_since_mode_switch
                        Pub().pub(
                            f"openWB/set/vehicle/{self.num}/control_parameter/imported_at_plan_start",
                            charged_since_mode_switch)
                else:
                    name = None
                required_current, submode, message, phases = self.charge_template.scheduled_charging_calc_current(
                    plan_data, self.data.get.soc, used_amount, max_phases)
                self.data.control_parameter.current_plan = name
                Pub().pub(f"openWB/set/vehicle/{self.num}/control_parameter/current_plan", name)

            # Wenn Zielladen auf Überschuss wartet, prüfen, ob Zeitladen aktiv ist.
            if ((required_current is None or required_current <= 1) and
                    self.charge_template.data.time_charging.active):
                time_charging_current, submode, message, name = self.charge_template.time_charging()
                if time_charging_current > 0:
                    self.data.control_parameter.current_plan = name
                    Pub().pub(f"openWB/set/vehicle/{self.num}/control_parameter/current_plan", name)
                    required_current = time_charging_current
            if (required_current == 0) or (required_current is None):
                if self.charge_template.data.chargemode.selected == "instant_charging":
                    # Wenn der Submode auf stop gestellt wird, wird auch die Energiemenge seit Moduswechsel
                    # zurückgesetzt, dann darf nicht die Energiemenge erneute geladen werden.
                    if (self.charge_template.data.chargemode.instant_charging.limit.selected == "amount" and
                            charged_since_mode_switch > self.data.control_parameter.used_amount_instant_charging):
                        self.data.control_parameter.used_amount_instant_charging = charged_since_mode_switch
                        Pub().pub(
                            f"openWB/set/vehicle/{self.num}/control_parameter/used_amount_instant_charging",
                            charged_since_mode_switch)
                    required_current, submode, message = self.charge_template.instant_charging(
                        self.data.get.soc,
                        self.data.control_parameter.used_amount_instant_charging)
                elif self.charge_template.data.chargemode.selected == "pv_charging":
                    required_current, submode, message = self.charge_template.pv_charging(
                        self.data.get.soc)
                elif self.charge_template.data.chargemode.selected == "standby":
                    # Text von Zeit-und Zielladen nicht überschreiben.
                    if message is None:
                        required_current, submode, message = self.charge_template.standby()
                    else:
                        required_current, submode, _ = self.charge_template.standby()
                elif self.charge_template.data.chargemode.selected == "stop":
                    required_current, submode, message = self.charge_template.stop()
            if submode == "stop" or (self.charge_template.data.chargemode.selected == "stop"):
                state = False
            if phases is None:
                phases = self.data.control_parameter.phases
            return state, message, submode, required_current, phases
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))
            return False, "ein interner Fehler aufgetreten ist.", "stop", 0, self.data.control_parameter.phases

    def check_state(self, required_current: float, set_current: float) -> Tuple[bool, bool]:
        """ prüft, ob sich etwas an den Parametern für die Regelung geändert hat,
        sodass der LP neu in die Priorisierung eingeordnet werden muss und veröffentlicht die Regelparameter.
        """
        try:
            current_changed = False
            mode_changed = False

            if self.data.control_parameter.chargemode != self.charge_template.data.chargemode.selected:
                mode_changed = True

            # Die benötigte Stromstärke hat sich durch eine Änderung des Lademodus oder der Konfiguration geändert.
            # Der Ladepunkt muss in der Regelung neu priorisiert werden.
            if self.data.control_parameter.required_current != required_current:
                # Wenn im PV-Laden mit übrigem Überschuss geladen wird und dadurch die aktuelle Soll-Stromstärke über
                # der neuen benötigten Stromstärke liegt, muss der LP im Algorithmus nicht neu eingeordnet werden, da
                # der LP mit der bisherigen Stormstärke weiter laden kann und sich die benötigte Stromstärke nur auf
                # die Reihenfolge innerhalb des Prioritäten-Tupels bezieht und auf dieser Ebene kein LP, der bereits
                # lädt, für einen neu hinzugekommenen abgeschaltet werden darf. Wenn sich auch der Lademodus geändert
                # hat, muss die neue Stromstärke in jedem Fall berücksichtigt werden.
                if ((self.charge_template.data.chargemode.selected == "pv_charging" or
                        self.charge_template.data.chargemode.selected == "scheduled_charging") and
                        ((self.data.control_parameter.submode == "pv_charging" or
                          self.data.control_parameter.chargemode == "pv_charging") and
                         set_current > self.data.control_parameter.required_current)):
                    current_changed = False
                else:
                    current_changed = True

            log.debug("Änderung der Sollstromstärke :" +
                      str(current_changed)+", Änderung des Lademodus :"+str(mode_changed))
            return current_changed, mode_changed
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))
            return True

    def set_control_parameter(self, submode, required_current):
        """ setzt die Regel-Parameter, die der Algorithmus verwendet.

        Parameter
        ---------
        submode: str
            neuer Lademodus, in dem geladen werden soll
        """
        try:
            self.data.control_parameter.submode = submode
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/submode", submode)
            self.data.control_parameter.chargemode = self.charge_template.data.chargemode.selected
            Pub().pub("openWB/set/vehicle/"+str(self.num)+"/control_parameter/chargemode",
                      self.charge_template.data.chargemode.selected)
            self.data.control_parameter.prio = self.charge_template.data.prio
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/prio", self.charge_template.data.prio)
            self.data.control_parameter.required_current = required_current
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/required_current", required_current)
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))

    def check_min_max_current(self, required_current, phases, pv=False):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom und unter dem Maximal-Ladestrom des EVs liegt.
        Falls nicht, wird der Ladestrom auf den Mindest-Ladestrom bzw. den Maximal-Ladestrom des EV gesetzt.
        Wenn PV-Laden aktiv ist, darf die Stromstärke nicht unter den PV-Mindeststrom gesetzt werden.

        Parameter
        ---------
        required_current: float
            Strom, der vom Lademodus benötigt wird

        phases: int
            Anzahl Phasen, mit denen geladen werden soll

        pv: bool
            Lademodus PV-Laden

        Return
        ------
        float: Strom, mit dem das EV laden darf
        """
        try:
            required_current_prev = required_current
            # Überprüfung bei 0 (automatische Umschaltung) erfolgt nach der Prüfung der Phasenumschaltung, wenn fest
            # steht, mit vielen Phasen geladen werden soll.
            if phases != 0:
                # EV soll/darf nicht laden
                if required_current != 0:
                    if not pv:
                        min_current = self.ev_template.data.min_current
                    else:
                        min_current = self.data.control_parameter.required_current
                    if required_current < min_current:
                        required_current = min_current
                    else:
                        if phases == 1:
                            max_current = self.ev_template.data.max_current_one_phase
                        else:
                            max_current = self.ev_template.data.max_current_multi_phases
                        if required_current > max_current:
                            required_current = max_current
            if required_current != required_current_prev:
                log.debug("Anpassen der Sollstromstärke an EV-Vorgaben. Sollstromstärke: " +
                          str(required_current_prev)+" neue Sollstromstärke: "+str(required_current))
            return required_current
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))
            return 0

    def auto_phase_switch(self,
                          cp_num: int,
                          get_currents: List[float],
                          get_power: float) -> Tuple[int, float, Optional[str]]:
        message = None
        current = self.data.control_parameter.required_current
        # Manche EV laden mit 6.1A bei 6A Sollstrom
        min_current = self.ev_template.data.min_current + 1
        max_current = self.ev_template.data.max_current_one_phase - self.ev_template.data.nominal_difference
        timestamp_auto_phase_switch = self.data.control_parameter.timestamp_auto_phase_switch
        phases_to_use = self.data.control_parameter.phases
        phases_in_use = self.data.control_parameter.phases
        pv_config = data.data.general_data.data.chargemode_config.pv_charging
        max_phases_ev = self.ev_template.data.max_phases
        if self.charge_template.data.chargemode.pv_charging.feed_in_limit:
            feed_in_yield = pv_config.feed_in_yield
        else:
            feed_in_yield = 0
        # verbleibender EVU-Überschuss unter Berücksichtigung der Einspeisegrenze und Speicherleistung
        all_overhang = data.data.pv_data["all"].data["set"]["available_power"] - \
            data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] + \
            data.data.bat_data["all"].power_for_bat_charging() + feed_in_yield
        if phases_in_use == 1:
            direction_str = "Umschaltverzögerung von 1 auf 3"
            delay = pv_config.phase_switch_delay * 60
            required_power = self.ev_template.data.min_current * max_phases_ev * \
                230 - self.ev_template.data.max_current_one_phase * 230
            new_phase = 3
            new_current = self.ev_template.data.min_current
        else:
            direction_str = "Umschaltverzögerung von 3 auf 1"
            delay = (16 - pv_config.phase_switch_delay) * 60
            required_power = self.ev_template.data.max_current_one_phase * \
                230 - self.ev_template.data.min_current * max_phases_ev * 230
            new_phase = 1
            new_current = self.ev_template.data.max_current_one_phase

        log.debug(
            f'Genutzter Strom: {max(get_currents)}A, Überschuss: {all_overhang}W, benötigte neue Leistung: '
            f'{required_power}W')
        # Wenn gerade umgeschaltet wird, darf kein Timer gestartet werden.
        if (not self.ev_template.data.prevent_phase_switch and
                self.data.control_parameter.timestamp_perform_phase_switch is None):
            if timestamp_auto_phase_switch is None:
                condition_1_to_3 = (max(get_currents) > max_current and
                                    all_overhang > self.ev_template.data.min_current * max_phases_ev * 230
                                    - get_power and
                                    phases_in_use == 1)
                condition_3_to_1 = max(get_currents) < min_current and all_overhang < 0 and phases_in_use == 3
                if condition_3_to_1 or condition_1_to_3:
                    # Umschaltverzögerung starten
                    timestamp_auto_phase_switch = timecheck.create_timestamp()
                    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] += required_power
                    message = f'{direction_str} Phasen für {delay/60} Min aktiv.'
            else:
                condition_1_to_3 = max(get_currents) > max_current and all_overhang > 0 and phases_in_use == 1
                condition_3_to_1 = max(get_currents) < min_current and all_overhang + \
                    required_power < 0 and phases_in_use == 3
                if condition_3_to_1 or condition_1_to_3:
                    # Timer laufen lassen
                    if timecheck.check_timestamp(timestamp_auto_phase_switch, delay):
                        message = f'{direction_str} Phasen für {delay/60} Min aktiv.'
                    else:
                        timestamp_auto_phase_switch = None
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= required_power
                        phases_to_use = new_phase
                        current = new_current
                        log.debug("Phasenumschaltung kann nun durchgeführt werden.")
                else:
                    timestamp_auto_phase_switch = None
                    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= required_power
                    message = f"{direction_str} Phasen abgebrochen."

        if message:
            log.info(f"LP {cp_num}: {message}")
        if timestamp_auto_phase_switch != self.data.control_parameter.timestamp_auto_phase_switch:
            self.data.control_parameter.timestamp_auto_phase_switch = timestamp_auto_phase_switch
            Pub().pub(f"openWB/set/vehicle/{self.num}/control_parameter/timestamp_auto_phase_switch",
                      timestamp_auto_phase_switch)
        return phases_to_use, current, message

    def reset_phase_switch(self):
        """ Zurücksetzen der Zeitstempel und reservierten Leistung.

        Die Phasenumschaltung kann nicht abgebrochen werden!
        """
        if self.data.control_parameter.timestamp_auto_phase_switch is not None:
            self.data.control_parameter.timestamp_auto_phase_switch = None
            Pub().pub("openWB/set/vehicle/"+str(self.num) +
                      "/control_parameter/timestamp_auto_phase_switch", None)
            # Wenn der Timer läuft, ist den Control-Paranetern die alte Phasenzahl hinterlegt.
            if self.data.control_parameter.phases == 3:
                reserved = self.ev_template.data.max_current_one_phase * \
                    230 - self.data.control_parameter.required_current * 3 * 230
                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= reserved
                log.debug(
                    "Zurücksetzen der reservierten Leistung für die Phasenumschaltung. reservierte Leistung: " +
                    str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))
            else:
                reserved = self.data.control_parameter.required_current * \
                    3 * 230 - self.ev_template.data.max_current_one_phase * 230
                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= reserved
                log.debug(
                    "Zurücksetzen der reservierten Leistung für die Phasenumschaltung. reservierte Leistung: " +
                    str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))

    def load_default_profile(self):
        """ prüft, ob nach dem Abstecken das Standardprofil geladen werden soll und lädt dieses ggf..
        """
        pass

    def lock_cp(self):
        """prüft, ob nach dem Abstecken der LP gesperrt werden soll und sperrt diesen ggf..
        """
        pass


@dataclass
class SelectedPlan:
    remaining_time: float = 0
    available_current: float = 14
    max_current: int = 16
    phases: int = 1
    num: int = 0


class ChargeTemplate:
    """ Klasse der Lademodus-Vorlage
    """
    BUFFER = -1200  # nach mehr als 20 Min Überschreitung wird der Termin als verpasst angesehen

    def __init__(self, index):
        self.data: ChargeTemplateData = ChargeTemplateData()
        self.ct_num = index

    TIME_CHARGING_NO_PLAN_CONFIGURED = "Keine Ladung, da keine Zeitfenster für Zeitladen konfiguriert sind."
    TIME_CHARGING_NO_PLAN_ACTIVE = "Keine Ladung, da kein Zeitfenster für Zeitladen aktiv ist."

    def time_charging(self) -> Tuple[int, str, Optional[str], Optional[str]]:
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        message = None
        try:
            if self.data.time_charging.plans:
                plan = timecheck.check_plans_timeframe(self.data.time_charging.plans)
                if plan is not None:
                    return plan.current, "time_charging", message, plan.name
                else:
                    message = self.TIME_CHARGING_NO_PLAN_ACTIVE
            else:
                message = self.TIME_CHARGING_NO_PLAN_CONFIGURED
            log.debug(message)
            return 0, "stop", message, None
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), None

    INSTANT_CHARGING_PRICE_EXCEEDED = "Keine Ladung, da der aktuelle Strompreis über dem maximalen Strompreis liegt."
    INSTANT_CHARGING_SOC_REACHED = "Keine Ladung, da der Soc bereits erreicht wurde."
    INSTANT_CHARGING_AMOUNT_REACHED = "Keine Ladung, da die Energiemenge bereits geladen wurde."

    def instant_charging(self,
                         soc: float,
                         used_amount_instant_charging: float) -> Tuple[int, str, Optional[str]]:
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.
        """
        message = None
        try:
            instant_charging = self.data.chargemode.instant_charging
            if data.data.optional_data["optional"].data["et"]["active"]:
                if not data.data.optional_data["optional"].et_price_lower_than_limit():
                    return 0, "stop", self.INSTANT_CHARGING_PRICE_EXCEEDED
            if instant_charging.limit.selected == "none":
                return instant_charging.current, "instant_charging", message
            elif instant_charging.limit.selected == "soc":
                if soc < instant_charging.limit.soc:
                    return instant_charging.current, "instant_charging", message
                else:
                    return 0, "stop", self.INSTANT_CHARGING_SOC_REACHED
            elif instant_charging.limit.selected == "amount":
                if used_amount_instant_charging < self.data.chargemode.instant_charging.limit.amount:
                    return instant_charging.current, "instant_charging", message
                else:
                    return 0, "stop", self.INSTANT_CHARGING_AMOUNT_REACHED
            else:
                raise TypeError(f'{instant_charging.limit.selected} unbekanntes Sofortladen-Limit.')
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    PV_CHARGING_SOC_REACHED = "Keine Ladung, da der maximale Soc bereits erreicht wurde."

    def pv_charging(self, soc: float) -> Tuple[int, str, Optional[str]]:
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.
        """
        message = None
        try:
            pv_charging = self.data.chargemode.pv_charging
            if soc < pv_charging.max_soc:
                if pv_charging.min_soc != 0:
                    if soc < pv_charging.min_soc:
                        return pv_charging.min_soc_current, "instant_charging", message
                if pv_charging.min_current == 0:
                    # nur PV; Ampere darf nicht 0 sein, wenn geladen werden soll
                    return 1, "pv_charging", message
                else:
                    # Min PV
                    return pv_charging.min_current, "instant_charging", message
            else:
                return 0, "stop", self.PV_CHARGING_SOC_REACHED
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def scheduled_charging_recent_plan(self,
                                       soc: float,
                                       ev_template: EvTemplate,
                                       phases: int,
                                       used_amount: float,
                                       max_phases: int,
                                       phase_switch_supported: bool) -> Optional[SelectedPlan]:
        """ prüft, ob der Ziel-SoC oder die Ziel-Energiemenge erreicht wurde und stellt den zur Erreichung nötigen
        Ladestrom ein. Um etwas mehr Puffer zu haben, wird bis 20 Min nach dem Zieltermin noch geladen, wenn dieser
        nicht eingehalten werden konnte.
        """
        if phase_switch_supported and data.data.general_data.get_phases_chargemode("scheduled_charging") == 0:
            max_current = ev_template.data.max_current_multi_phases
            plan_data = self.search_plan(max_current, soc, ev_template, max_phases, used_amount)
            if plan_data:
                if plan_data.remaining_time > 300:
                    max_current = ev_template.data.max_current_one_phase
                    plan_data = self.search_plan(max_current, soc, ev_template, 1, used_amount)
        else:
            if phases == 1:
                max_current = ev_template.data.max_current_one_phase
            else:
                max_current = ev_template.data.max_current_multi_phases
            plan_data = self.search_plan(max_current, soc, ev_template, phases, used_amount)
        return plan_data

    def search_plan(self,
                    max_current: int,
                    soc: float,
                    ev_template: EvTemplate,
                    phases: int,
                    used_amount: float) -> Optional[SelectedPlan]:
        smallest_remaining_time = float("inf")
        missed_date_today_of_plan_with_smallest_remaining_time = False
        plan_data: Optional[SelectedPlan] = None
        battery_capacity = ev_template.data.battery_capacity
        for num, plan in self.data.chargemode.scheduled_charging.plans.items():
            if plan.active:
                try:
                    duration = self.calculate_duration(plan, soc, battery_capacity, used_amount, phases)
                    remaining_time, missed_date_today = timecheck.check_duration(plan, duration, self.BUFFER)
                    if remaining_time:
                        # Wenn der Zeitpunkt vorüber, aber noch nicht abgelaufen ist oder
                        # wenn noch gar kein Plan vorhanden ist,
                        if ((remaining_time < 0 and (missed_date_today is False or not plan_data)) or
                                # oder der Zeitpunkt noch nicht vorüber ist
                                remaining_time > 0):
                            # Wenn die verbleibende Zeit geringer als die niedrigste bisherige verbleibende Zeit ist
                            if (remaining_time < smallest_remaining_time or
                                    # oder wenn der Zeitpunkt abgelaufen ist und es noch einen Zeitpunkt gibt, der in
                                    # der Zukunft liegt.
                                    (missed_date_today_of_plan_with_smallest_remaining_time and 0 < remaining_time)):
                                smallest_remaining_time = remaining_time
                                missed_date_today_of_plan_with_smallest_remaining_time = missed_date_today
                                plan_data = SelectedPlan(
                                    remaining_time=remaining_time,
                                    available_current=plan.current,
                                    max_current=max_current,
                                    phases=phases,
                                    num=num)
                    log.debug(f"Plan-Nr. {num}: Differenz zum Start {remaining_time}s, Dauer {duration}h, "
                              f"Termin heute verpasst: {missed_date_today}")
                except Exception:
                    log.exception("Fehler im ev-Modul "+str(self.ct_num))
        return plan_data

    def calculate_duration(self,
                           plan: ScheduledChargingPlan,
                           soc: float,
                           battery_capacity: float,
                           used_amount: float,
                           phases: int) -> float:
        if plan.limit.selected == "soc":
            missing_amount = ((plan.limit.soc_scheduled - soc) / 100) * battery_capacity * 1000
        else:
            missing_amount = plan.limit.amount - used_amount
        duration = missing_amount/(plan.current * phases*230)
        return duration

    SCHEDULED_CHARGING_REACHED_LIMIT_SOC = "Keine Ladung, da der Ziel-Soc und das SoC-Limit bereits erreicht wurden."
    SCHEDULED_CHARGING_REACHED_AMOUNT = "Keine Ladung, da die Energiemenge bereits erreicht wurde."
    SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC = ("Falls vorhanden wird mit EVU-Überschuss geladen, da der Ziel-Soc "
                                                "bereits erreicht wurde.")
    SCHEDULED_CHARGING_NO_PLANS_CONFIGURED = "Keine Ladung, da keine Ziel-Termine konfiguriert sind."
    SCHEDULED_CHARGING_USE_PV = ("Kein Sofortladen, da noch Zeit bis zum Zieltermin ist. Falls vorhanden, "
                                 "wird mit EVU-Überschuss geladen.")
    SCHEDULED_CHARGING_MAX_CURRENT = ("Zielladen mit {}A. Der verfügbare Ladezeitraum reicht nicht aus, um "
                                      "das zu erreichen. Daher wird bis max. 20 Minuten nach dem angegebenen "
                                      "Zieltermin geladen.")
    SCHEDULED_CHARGING_LIMITED_BY_SOC = 'einen SoC von {}%'
    SCHEDULED_CHARGING_LIMITED_BY_AMOUNT = '{}kWh geladene Energie'
    SCHEDULED_CHARGING_IN_TIME = 'Zielladen mit {}A, um {}  um {} zu erreichen.'

    def scheduled_charging_calc_current(self,
                                        plan_data: Optional[SelectedPlan],
                                        soc: int,
                                        used_amount: float,
                                        max_phases: int) -> Tuple[float, str, str, int]:
        current = 0
        mode = "stop"
        if plan_data is None:
            return current, mode, self.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, max_phases
        current_plan = self.data.chargemode.scheduled_charging.plans[plan_data.num]
        limit = current_plan.limit
        phases = plan_data.phases
        log.debug("Verwendeter Plan: "+str(current_plan.name))
        if limit.selected == "soc" and soc >= limit.soc_limit:
            message = self.SCHEDULED_CHARGING_REACHED_LIMIT_SOC
        elif limit.selected == "soc" and limit.soc_scheduled <= soc < limit.soc_limit:
            message = self.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC
            current = 1
            mode = "pv_charging"
        elif limit.selected == "amount" and used_amount >= limit.amount:
            message = self.SCHEDULED_CHARGING_REACHED_AMOUNT
        elif 0 < plan_data.remaining_time < 300:  # 5 Min vor spätestem Ladestart
            if limit.selected == "soc":
                limit_string = self.SCHEDULED_CHARGING_LIMITED_BY_SOC.format(limit.soc_scheduled)
            else:
                limit_string = self.SCHEDULED_CHARGING_LIMITED_BY_AMOUNT.format(limit.amount/1000)
            message = self.SCHEDULED_CHARGING_IN_TIME.format(
                plan_data.available_current, limit_string, current_plan.time)
            current = plan_data.available_current
            mode = "instant_charging"
            phases = max_phases
        # weniger als die berechnete Zeit verfügbar
        elif plan_data.remaining_time <= 0:  # Ladestart wurde um maximal 20 Min verpasst.
            message = self.SCHEDULED_CHARGING_MAX_CURRENT.format(plan_data.max_current)
            current = plan_data.max_current
            mode = "instant_charging"
            phases = max_phases
        else:
            # Wenn Elektronische Tarife aktiv sind, prüfen, ob jetzt ein günstiger Zeitpunkt zum Laden
            # ist.
            if data.data.optional_data["optional"].data["et"]["active"]:
                hourlist = data.data.optional_data["optional"].et_get_loading_hours(
                    plan_data.remaining_time)
                if timecheck.is_list_valid(hourlist):
                    message = "Sofortladen, da ein günstiger Zeitpunkt zum preisbasierten Laden ist."
                    current = plan_data.available_current
                    mode = "instant_charging"
                    phases = max_phases
                else:
                    message = ("Kein Sofortladen, da kein günstiger Zeitpunkt zum preisbasierten Laden "
                               "ist. Falls vorhanden, wird mit EVU-Überschuss geladen.")
                    current = 1
                    mode = "pv_charging"
            else:
                message = self.SCHEDULED_CHARGING_USE_PV
                current = 1
                mode = "pv_charging"
        return current, mode, message, phases

    def standby(self) -> Tuple[int, str, str]:
        return 0, "standby", "Keine Ladung, da der Lademodus Standby aktiv ist."

    def stop(self) -> Tuple[int, str, str]:
        return 0, "stop", "Keine Ladung, da der Lademodus Stop aktiv ist."


def get_ev_to_rfid(rfid):
    """ sucht zur übergebenen RFID-ID das EV.

    Parameter
    ---------
    rfid: int
        Tag-ID

    Return
    ------
    vehicle: int
        Nummer des EV, das zum Tag gehört
    """
    for vehicle in data.data.ev_data:
        try:
            if "ev" in vehicle:
                if rfid in data.data.ev_data[vehicle].data.tag_id:
                    return data.data.ev_data[vehicle].num
        except Exception:
            log.exception("Fehler im ev-Modul "+vehicle)
            return None
    else:
        return None
