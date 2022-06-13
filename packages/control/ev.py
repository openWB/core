""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.

In den control Parametern wird sich der Lademodus, Submodus, Priorität, Phasen und Stromstärke gemerkt,
mit denen das EV aktuell in der Regelung berücksichtigt wird. Bei der Ermittlung der benötigten Strom-
stärke wird auch geprüft, ob sich an diesen Parametern etwas geändert hat. Falls ja, muss das EV
in der Regelung neu priorisiert werden und eine neue Zuteilung des Stroms erhalten.
"""
import logging
import traceback
from typing import List, Dict, Optional, Tuple, Union

from control import data
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
                if rfid in data.data.ev_data[vehicle].data["tag_id"]:
                    return data.data.ev_data[vehicle].ev_num
        except Exception:
            log.exception("Fehler im ev-Modul "+vehicle)
            return data.data.ev_data[0].ev_num
    else:
        return None


class Ev:
    """Logik des EV
    """

    def __init__(self, index):
        try:
            self.ev_template: EvTemplate
            self.charge_template: ChargeTemplate
            self.soc_module: AbstractSoc = None
            self.ev_num = index
            self.data = {"set": {},
                         "control_parameter": {"required_current": 0,
                                               "phases": 0,
                                               "prio": False,
                                               "timestamp_switch_on_off": None,
                                               "timestamp_auto_phase_switch": None,
                                               "timestamp_perform_phase_switch": None,
                                               "submode": "stop",
                                               "chargemode": "stop",
                                               "used_amount_instant_charging": 0,
                                               "imported_at_plan_start": 0,
                                               "current_plan": None}}
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ev_num))

    def reset_ev(self):
        """ setzt alle Werte zurück, die während des Algorithmus gesetzt werden.
        """
        try:
            log.debug("EV "+str(self.ev_num)+" zurückgesetzt.")
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/required_current", 0)
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/timestamp_auto_phase_switch", None)
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/timestamp_perform_phase_switch", None)
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/submode", "stop")
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/chargemode", "stop")
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/used_amount_instant_charging", 0)
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/imported_at_plan_start", 0)
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/current_plan", None)
            self.data["control_parameter"].update({"required_current": 0,
                                                   "timestamp_auto_phase_switch": None,
                                                  "timestamp_perform_phase_switch": None,
                                                   "submode": "stop",
                                                   "chargemode": "stop",
                                                   "used_amount_instant_charging": 0,
                                                   "imported_at_plan_start": 0,
                                                   "current_plan": None})
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ev_num))

    def get_required_current(self, charged_since_mode_switch: float) -> Tuple[bool, str, str, float]:
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
        submode = None
        required_current = None
        message = None
        state = True
        try:
            if self.charge_template.data["chargemode"]["selected"] == "scheduled_charging":
                used_amount = charged_since_mode_switch - self.data["control_parameter"]["imported_at_plan_start"]
                plan_data = self.charge_template.scheduled_charging_recent_plan(
                    self.data["get"]["soc"], self.ev_template, self.data["control_parameter"]["phases"], used_amount)
                if plan_data["num"]:
                    name = self.charge_template.data["chargemode"]["scheduled_charging"]["plans"][plan_data["num"]][
                        "name"]
                else:
                    name = None
                # Wenn mit einem neuen Plan geladen wird, muss auch die Energiemenge von neuem gezählt werden.
                if self.charge_template.data["chargemode"]["scheduled_charging"]["plans"][plan_data["num"]]["limit"][
                        "selected"] == "amount" and name != self.data["control_parameter"]["current_plan"]:
                    self.data["control_parameter"]["imported_at_plan_start"] = charged_since_mode_switch
                    Pub().pub(
                        "openWB/set/vehicle/{self.ev_num}/control_parameter/imported_at_plan_start",
                        charged_since_mode_switch)
                required_current, submode, message = self.charge_template.scheduled_charging_calc_current(
                    plan_data, self.data["get"]["soc"], used_amount)
                self.data["control_parameter"]["current_plan"] = name
                Pub().pub("openWB/set/vehicle/{self.ev_num}/control_parameter/current_plan", name)

            elif self.charge_template.data["time_charging"]["active"]:
                required_current, submode, message, name = self.charge_template.time_charging()
                self.data["control_parameter"]["current_plan"] = name
                Pub().pub("openWB/set/vehicle/{self.ev_num}/control_parameter/current_plan", name)
            if (required_current == 0) or (required_current is None):
                if self.charge_template.data["chargemode"]["selected"] == "instant_charging":
                    # Wenn der Submode auf stop gestellt wird, wird auch die Energiemenge seit Moduswechsel
                    # zurückgesetzt, dann darf nicht die Energiemenge erneute geladen werden.
                    if (self.charge_template.data["chargemode"]["instant_charging"]["limit"][
                            "selected"] == "amount" and charged_since_mode_switch > self.data["control_parameter"][
                            "used_amount_instant_charging"]):
                        self.data["control_parameter"]["used_amount_instant_charging"] = charged_since_mode_switch
                        Pub().pub(
                            f"openWB/set/vehicle/{self.ev_num}/control_parameter/used_amount_instant_charging",
                            charged_since_mode_switch)
                    required_current, submode, message = self.charge_template.instant_charging(
                        self.data["get"]["soc"],
                        self.data["control_parameter"]["used_amount_instant_charging"])
                elif self.charge_template.data["chargemode"]["selected"] == "pv_charging":
                    required_current, submode, message = self.charge_template.pv_charging(
                        self.data["get"]["soc"])
                elif self.charge_template.data["chargemode"]["selected"] == "standby":
                    # Text von Zeit-und Zielladen nicht überschreiben.
                    if message is None:
                        required_current, submode, message = self.charge_template.standby()
                    else:
                        required_current, submode, _ = self.charge_template.standby()
                elif self.charge_template.data["chargemode"]["selected"] == "stop":
                    required_current, submode, message = self.charge_template.stop()
            if submode == "stop" or (self.charge_template.data["chargemode"]["selected"] == "stop"):
                state = False

            return state, message, submode, required_current
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ev_num))
            return False, "ein interner Fehler aufgetreten ist: "+traceback.format_exc(), "stop", 0

    def check_state(self, required_current, set_current, charge_state):
        """ prüft, ob sich etwas an den Parametern für die Regelung geändert hat,
        sodass der LP neu in die Priorisierung eingeordnet werden muss und veröffentlicht die Regelparameter.

        Parameter
        ---------
        required_current: int
            neue Stromstärke, mit der geladen werden soll

        set_current: int
            Soll-Stromstärke

        Return
        ------
        current_changed: bool
            Die Sollstromstärke wurde geändert.
        mode_changed: bool
            Der Lademodus wurde geändert.
        """
        try:
            current_changed = False
            mode_changed = False

            if self.data["control_parameter"]["chargemode"] != self.charge_template.data["chargemode"]["selected"]:
                mode_changed = True

            # Die benötigte Stromstärke hat sich durch eine Änderung des Lademodus oder der Konfiguration geändert.
            # Der Ladepunkt muss in der Regelung neu priorisiert werden.
            if self.data["control_parameter"]["required_current"] != required_current:
                # Wenn im PV-Laden mit übrigem Überschuss geladen wird und dadurch die aktuelle Soll-Stromstärke über
                # der neuen benötigten Stromstärke liegt, muss der LP im Algorithmus nicht neu eingeordnet werden, da
                # der LP mit der bisherigen Stormstärke weiter laden kann und sich die benötigte Stromstärke nur auf
                # die Reihenfolge innerhalb des Prioritäten-Tupels bezieht und auf dieser Ebene kein LP, der bereits
                # lädt, für einen neu hinzugekommenen abgeschaltet werden darf. Wenn sich auch der Lademodus geändert
                # hat, muss die neue Stromstärke in jedem Fall berücksichtigt werden.
                if ((self.charge_template.data["chargemode"]["selected"] == "pv_charging" or
                        self.charge_template.data["chargemode"]["selected"] == "scheduled_charging") and
                        ((self.data["control_parameter"]["submode"] == "pv_charging" or
                          self.data["control_parameter"]["chargemode"] == "pv_charging") and
                         set_current > self.data["control_parameter"]["required_current"])):
                    current_changed = False
                else:
                    current_changed = True

            log.debug("Änderung der Sollstromstärke :" +
                      str(current_changed)+", Änderung des Lademodus :"+str(mode_changed))
            return current_changed, mode_changed
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ev_num))
            return True

    def set_control_parameter(self, submode, required_current):
        """ setzt die Regel-Parameter, die der Algorithmus verwendet.

        Parameter
        ---------
        submode: str
            neuer Lademodus, in dem geladen werden soll
        """
        try:
            self.data["control_parameter"]["submode"] = submode
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/submode", submode)
            self.data["control_parameter"]["chargemode"] = self.charge_template.data["chargemode"]["selected"]
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num)+"/control_parameter/chargemode",
                      self.charge_template.data["chargemode"]["selected"])
            self.data["control_parameter"]["prio"] = self.charge_template.data["prio"]
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/prio", self.charge_template.data["prio"])
            self.data["control_parameter"]["required_current"] = required_current
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/required_current", required_current)
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ev_num))

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
                        min_current = self.ev_template.data["min_current"]
                    else:
                        min_current = self.data["control_parameter"]["required_current"]
                    if required_current < min_current:
                        required_current = min_current
                    else:
                        if phases == 1:
                            max_current = self.ev_template.data["max_current_one_phase"]
                        else:
                            max_current = self.ev_template.data["max_current_multi_phases"]
                        if required_current > max_current:
                            required_current = max_current
            if required_current != required_current_prev:
                log.debug("Anpassen der Sollstromstärke an EV-Vorgaben. Sollstromstärke: " +
                          str(required_current_prev)+" neue Sollstromstärke: "+str(required_current))
            return required_current
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ev_num))
            return 0

    def auto_phase_switch(self,
                          cp_num: int,
                          get_currents: List[float],
                          get_power: float) -> Tuple[int, float, Optional[str]]:
        message = None
        current = self.data["control_parameter"]["required_current"]
        # Manche EV laden mit 6.1A bei 6A Sollstrom
        min_current = self.ev_template.data["min_current"] + 1
        max_current = self.ev_template.data["max_current_one_phase"] - self.ev_template.data["nominal_difference"]
        timestamp_auto_phase_switch = self.data["control_parameter"]["timestamp_auto_phase_switch"]
        phases_to_use = self.data["control_parameter"]["phases"]
        phases_in_use = self.data["control_parameter"]["phases"]
        pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
        max_phases_ev = self.ev_template.data["max_phases"]
        if self.charge_template.data["chargemode"]["pv_charging"]["feed_in_limit"]:
            feed_in_yield = pv_config["feed_in_yield"]
        else:
            feed_in_yield = 0
        # verbleibender EVU-Überschuss unter Berücksichtigung der Einspeisegrenze und Speicherleistung
        all_overhang = data.data.pv_data["all"].data["set"]["available_power"] - \
            data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] + \
            data.data.bat_data["all"].power_for_bat_charging() + feed_in_yield
        if phases_in_use == 1:
            direction_str = "Umschaltverzögerung von 1 auf 3"
            delay = pv_config["phase_switch_delay"] * 60
            required_power = self.ev_template.data["min_current"] * max_phases_ev * \
                230 - self.ev_template.data["max_current_one_phase"] * 230
            new_phase = 3
            new_current = self.ev_template.data["min_current"]
        else:
            direction_str = "Umschaltverzögerung von 3 auf 1"
            delay = (16 - pv_config["phase_switch_delay"]) * 60
            required_power = self.ev_template.data["max_current_one_phase"] * \
                230 - self.ev_template.data["min_current"] * max_phases_ev * 230
            new_phase = 1
            new_current = self.ev_template.data["max_current_one_phase"]

        log.debug(
            f'Genutzter Strom: {max(get_currents)}A, Überschuss: {all_overhang}W, benötigte neue Leistung: '
            f'{required_power}W')
        # Wenn gerade umgeschaltet wird, darf kein Timer gestartet werden.
        if not self.ev_template.data["prevent_phase_switch"] and self.data["control_parameter"][
                "timestamp_perform_phase_switch"] is None:
            if timestamp_auto_phase_switch is None:
                condition_1_to_3 = (max(get_currents) > max_current and
                                    all_overhang > self.ev_template.data[
                                        "min_current"] * max_phases_ev * 230 - get_power and
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
        if timestamp_auto_phase_switch != self.data["control_parameter"]["timestamp_auto_phase_switch"]:
            self.data["control_parameter"]["timestamp_auto_phase_switch"] = timestamp_auto_phase_switch
            Pub().pub(f"openWB/set/vehicle/{self.ev_num}/control_parameter/timestamp_auto_phase_switch",
                      timestamp_auto_phase_switch)
        return phases_to_use, current, message

    def reset_phase_switch(self):
        """ Zurücksetzen der Zeitstempel und reservierten Leistung.

        Die Phasenumschaltung kann nicht abgebrochen werden!
        """
        if self.data["control_parameter"]["timestamp_auto_phase_switch"] is not None:
            self.data["control_parameter"]["timestamp_auto_phase_switch"] = None
            Pub().pub("openWB/set/vehicle/"+str(self.ev_num) +
                      "/control_parameter/timestamp_auto_phase_switch", None)
            # Wenn der Timer läuft, ist den Control-Paranetern die alte Phasenzahl hinterlegt.
            if self.data["control_parameter"]["phases"] == 3:
                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.ev_template.data[
                    "max_current_one_phase"] * 230 - self.data["control_parameter"]["required_current"] * 3 * 230
                log.debug(
                    "Zurücksetzen der reservierten Leistung für die Phasenumschaltung. reservierte Leistung: " +
                    str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))
            else:
                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.data["control_parameter"][
                    "required_current"] * 3 * 230 - self.ev_template.data["max_current_one_phase"] * 230
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


def get_ev_template_default() -> dict:
    return {
        "name": "Standard-Fahrzeug-Vorlage",
        "max_current_multi_phases": 16,
        "max_phases": 3,
        "phase_switch_pause": 2,
        "prevent_phase_switch": False,
        "prevent_charge_stop": False,
        "control_pilot_interruption": False,
        "control_pilot_interruption_duration": 4,
        "average_consump": 17,
        "min_current": 6,
        "max_current_one_phase": 32,
        "battery_capacity": 82,
        "nominal_difference": 2,
        "soc": {
            "request_interval_charging": 5,
            "request_interval_not_charging": 720,
            "request_only_plugged": False
        }
    }


class EvTemplate:
    """ Klasse mit den EV-Daten
    """

    def __init__(self, index):
        self.data = {}
        self.et_num = index

    def soc_interval_expired(
            self, plug_state: bool, charge_state: bool, soc_timestamp: Union[str, None]) -> bool:
        request_soc = False
        if soc_timestamp is None:
            # Initiale Abfrage
            request_soc = True
        else:
            if (self.data["soc"]["request_only_plugged"] is False or
                    (self.data["soc"]["request_only_plugged"] is True and plug_state is True)):
                if charge_state is True:
                    interval = self.data["soc"]["request_interval_charging"]
                else:
                    interval = self.data["soc"]["request_interval_not_charging"]
                # Zeitstempel prüfen, ob wieder abgefragt werden muss.
                if timecheck.check_timestamp(soc_timestamp, interval*60-5) is False:
                    # Zeit ist abgelaufen
                    request_soc = True
        return request_soc


def get_charge_template_default() -> dict:
    return {
        "name": "Standard-Ladeprofil-Vorlage",
        "disable_after_unplug": False,
        "prio": False,
        "load_default": False,
        "time_charging":
            {
                "active": False,
            },
        "chargemode":
            {
                "selected": "stop",
                "pv_charging":
                {
                    "min_soc_current": 10,
                    "min_current": 0,
                    "feed_in_limit": False,
                    "min_soc": 0,
                    "max_soc": 100
                },
                "scheduled_charging":
                {
                },
                "instant_charging":
                {
                    "current": 10,
                    "limit":
                    {
                        "selected": "none",
                        "soc": 50,
                        "amount": 10000
                    }
                }
            }
    }


def get_charge_template_scheduled_plan_default() -> dict:
    charge_template_scheduled_plan_default = {
        "name": "Zielladen-Standard",
        "active": False,
        "time": "07:00",  # ToDo: aktuelle Zeit verwenden
        "limit":
            {
                "selected": "amount",
                "soc": 50,
                "amount": 10000
            },
        "frequency":
            {
                "selected": "daily",
                "once": ["2021-11-01"],  # ToDo: aktuelles Datum verwenden
                "weekly": [False, False, False, False, False, False, False]
            }
    }
    return charge_template_scheduled_plan_default


def get_charge_template_time_charging_plan_default():
    charge_template_time_charging_plan_default = {
        "name": "Zeitladen-Standard",
        "active": False,
        "time": ["06:00", "07:00"],  # ToDo: aktuelle Zeit verwenden + 1 Stunde
        "current": 16,
        "frequency":
        {
            "selected": "daily",
            "once": ["2021-11-01", "2021-11-05"],  # ToDo: aktuelles Datum verwenden
            "weekly": [False, False, False, False, False, False, False]
        }
    }
    return charge_template_time_charging_plan_default


class ChargeTemplate:
    """ Klasse der Lademodus-Vorlage
    """

    def __init__(self, index):
        self.data = {"chargemode": {"scheduled_charging": {"plans": {}}}, "time_charging": {"plans": {}}}
        self.ct_num = index

    def time_charging(self):
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        message = None
        try:
            if self.data["time_charging"]["plans"]:
                plan = timecheck.check_plans_timeframe(
                    self.data["time_charging"]["plans"])
                if plan is not None:
                    return plan["current"], "time_charging", message, plan["name"]
                else:
                    message = "Keine Ladung, da kein Zeitfenster aktiv ist."
                    return 0, "stop", message, None
            else:
                message = "Keine Ladung, da keine Zeitfenster für Zeitladen konfiguriert sind."
                return 0, "stop", message, None
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), None

    def instant_charging(self,
                         soc: int,
                         used_amount_instant_charging: float) -> Tuple[int, str, Optional[str]]:
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.
        """
        message = None
        try:
            instant_charging = self.data["chargemode"]["instant_charging"]
            if data.data.optional_data["optional"].data["et"]["active"]:
                if not data.data.optional_data["optional"].et_price_lower_than_limit():
                    message = "Keine Ladung, da der aktuelle Strompreis über dem maximalen Strompreis liegt."
                    return 0, "stop", message
            if instant_charging["limit"]["selected"] == "none":
                return instant_charging["current"], "instant_charging", message
            elif instant_charging["limit"]["selected"] == "soc":
                if soc < instant_charging["limit"]["soc"]:
                    return instant_charging["current"], "instant_charging", message
                else:
                    message = "Keine Ladung, da der Soc bereits erreicht wurde."
                    return 0, "stop", message
            elif instant_charging["limit"]["selected"] == "amount":
                if used_amount_instant_charging < self.data["chargemode"]["instant_charging"]["limit"]["amount"]:
                    return instant_charging["current"], "instant_charging", message
                else:
                    message = "Keine Ladung, da die Energiemenge bereits geladen wurde."
                    return 0, "stop", message
            else:
                raise TypeError(f'{instant_charging["limit"]["selected"]} unbekanntes Sofortladen-Limit.')
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def pv_charging(self, soc):
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.

        Parameter
        ---------
        soc: int
            SoC des EV

        Return
        ------
        Required Current, Chargemode: int, str
            Theoretisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        message = None
        try:
            pv_charging = self.data["chargemode"]["pv_charging"]
            if soc < pv_charging["max_soc"]:
                if pv_charging["min_soc"] != 0:
                    if soc < pv_charging["min_soc"]:
                        return pv_charging["min_soc_current"], "instant_charging", message
                if pv_charging["min_current"] == 0:
                    # nur PV; Ampere darf nicht 0 sein, wenn geladen werden soll
                    return 1, "pv_charging", message
                else:
                    # Min PV
                    return pv_charging["min_current"], "instant_charging", message
            else:
                message = "Keine Ladung, da der maximale Soc bereits erreicht wurde."
                return 0, "stop", message
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def scheduled_charging_recent_plan(self,
                                       soc: float,
                                       ev_template: EvTemplate,
                                       phases: int,
                                       used_amount: float) -> Dict:
        """ prüft, ob der Ziel-SoC oder die Ziel-Energiemenge erreicht wurde und stellt den zur Erreichung nötigen
        Ladestrom ein. Um etwas mehr Puffer zu haben, wird bis 20 Min nach dem Zieltermin noch geladen, wenn dieser
        nicht eingehalten werden konnte.
        """
        smallest_remaining_time = 0
        plan_data = {"start": -1, "num": None}
        battery_capacity = ev_template.data["battery_capacity"]
        start = -1  # Es wurde noch kein Plan geprüft.
        for num, plan in self.data["chargemode"]["scheduled_charging"]["plans"].items():
            if plan["active"]:
                try:
                    if phases == 1:
                        max_current = ev_template.data["max_current_one_phase"]
                    else:
                        max_current = ev_template.data["max_current_multi_phases"]
                    available_current = 0.8*max_current*phases
                    if plan["limit"]["selected"] == "soc":
                        missing_amount = ((plan["limit"]["soc"] - soc)/100) * battery_capacity*1000
                    else:
                        missing_amount = plan["limit"]["amount"] - used_amount
                    duration = missing_amount/(available_current*230)
                    start, remaining_time = timecheck.check_duration(plan, duration)
                    # Erster Plan
                    if ((start == plan_data["start"] and remaining_time <= smallest_remaining_time) or
                            start > plan_data["start"]):
                        smallest_remaining_time = remaining_time
                        plan_data["remaining_time"] = remaining_time
                        plan_data["available_current"] = available_current
                        plan_data["start"] = start
                        plan_data["required_wh"] = missing_amount
                        plan_data["max_current"] = max_current
                        plan_data["num"] = num
                except Exception:
                    log.exception("Fehler im ev-Modul "+str(self.ct_num))
        return plan_data

    def scheduled_charging_calc_current(self, plan_data: dict, soc: int, used_amount: float) -> Tuple[float, str, str]:
        if plan_data["num"] is None:
            message = "Keine Ladung, da keine Ziel-Termine konfiguriert sind."
            return 0, "stop", message
        current_plan = self.data["chargemode"]["scheduled_charging"]["plans"][plan_data["num"]]
        log.debug("Verwendeter Plan: "+str(current_plan["name"]))
        if current_plan["limit"]["selected"] == "soc" and soc >= current_plan["limit"]["soc"]:
            message = "Keine Ladung, da der Ziel-Soc bereits erreicht wurde."
            return 0, "stop", message
        if current_plan["limit"]["selected"] == "amount" and used_amount >= current_plan["limit"]["amount"]:
            message = "Keine Ladung, da die Energiemenge bereits erreicht wurde."
            return 0, "stop", message

        if plan_data["start"] == 1:  # Ladung sollte jetzt starten
            message = f'Zielladen mit {plan_data["available_current"]}A, um einen SoC von {current_plan["soc"]}%% um '
            f'{current_plan["time"]} zu erreichen.'
            return plan_data["available_current"], "instant_charging", message
        # weniger als die berechnete Zeit verfügbar
        elif plan_data["start"] == 2:
            required_current = plan_data["required_wh"] / \
                (plan_data["remaining_time"]*230)
            if required_current >= plan_data["max_current"]:
                current = plan_data["max_current"]
            else:
                current = required_current
            message = "Zielladen mit "+str(current) + \
                "A. Der verfügbare Ladezeitraum reicht nicht aus, um das zu erreichen. \
                Daher wird bis max. 20 Minuten nach dem angegebenen Zieltermin geladen."
            return current, "instant_charging", message
        else:
            # Liegt der Zieltermin innerhalb der nächsten 24h?
            if timecheck.check_timeframe(current_plan, 24):
                # Wenn Elektronische Tarife aktiv sind, prüfen, ob jetzt ein günstiger Zeitpunkt zum Laden
                # ist.
                if data.data.optional_data["optional"].data["et"]["active"]:
                    hourlist = data.data.optional_data["optional"].et_get_loading_hours(
                        plan_data["remaining_time"])
                    if timecheck.is_list_valid(hourlist):
                        message = "Sofortladen, da ein günstiger Zeitpunkt zum preisbasierten Laden \
                            ist."
                        return plan_data["available_current"], "instant_charging", message
                    else:
                        message = "Kein Sofortladen, da kein günstiger Zeitpunkt zum preisbasierten Laden \
                            ist. Falls vorhanden, wird mit EVU-Überschuss geladen."
                        return 1, "pv_charging", message
                else:
                    message = "Kein Sofortladen, da noch Zeit bis zum Zieltermin ist. Falls vorhanden, \
                        wird mit EVU-Überschuss geladen."
                    return 1, "pv_charging", message
            else:
                message = "Keine Ladung, da noch mehr als ein Tag bis zum Zieltermin ist. "
                return 0, "stop", message

    def standby(self):
        """ setzt den benötigten Strom auf 0.

        Return
        ------
            Required Current, Chargemode: int, str
                Theoretisch benötigter Strom, Ladmodus
        """
        message = "Keine Ladung, da der Lademodus Standby aktiv ist."
        return 0, "standby", message

    def stop(self):
        """ setzt den benötigten Strom auf 0.

        Return
        ------
            Required Current, Chargemode: int, str
                Theoretisch benötigter Strom, Ladmodus
        """
        message = "Keine Ladung, da der Lademodus Stop aktiv ist."
        return 0, "stop", message
