"""Ladepunkt-Logik

charging_ev: EV, das aktuell laden darf
charging_ev_prev: EV, das vorher geladen hat. Dies wird benötigt, da wenn das EV nicht mehr laden darf, z.B. weil
Autolock aktiv ist, gewartet werden muss, bis die Ladeleistung 0 ist und dann erst der Eintrag im Protokoll erstellt
werden kann.
charging_ev = -1 zeigt an, dass der LP im Algorithmus nicht berücksichtigt werden soll. Ist das Ev abgesteckt, wird
auch charging_ev_prev -1 und im nächsten Zyklus kann ein neues Profil geladen werden.

RFID-Tags/Code-Eingabe:
Mit einem Tag/Code kann optional der Ladepunkt freigeschaltet werden, es wird gleichzeitig immer ein EV damit
zugeordnet, mit dem nach der Freischaltung geladen werden soll. Wenn max 5 Min nach dem Scannen kein Auto
angesteckt wird, wird der Tag verworfen. Ebenso wenn kein EV gefunden wird.
Tag-Liste: Tags, mit denen der Ladepunkt freigeschaltet werden kann. Ist diese leer, kann mit jedem Tag der Ladepunkt
freigeschaltet werden.
"""
import copy
from dataclasses import dataclass, field
import dataclasses
import logging
from threading import Thread
import threading
import traceback
from typing import Dict, List, Optional, Tuple

from control import chargelog
from control import cp_interruption
from control import data
from control import ev as ev_module
from control.ev import Ev
from control import phase_switch
from helpermodules.pub import Pub
from helpermodules import timecheck
from modules.common.abstract_chargepoint import AbstractChargepoint


def get_chargepoint_default() -> dict:
    return {
        "name": "Standard-Ladepunkt",
        "type": None,
        "ev": 0,
        "template": 0,
        "connected_phases": 3,
        "phase_1": 0,
        "auto_phase_switch_hw": False,
        "control_pilot_interruption_hw": False
    }


log = logging.getLogger(__name__)


@dataclass
class AllGet:
    daily_imported: float = 0
    daily_exported: float = 0
    power: float = 0
    imported: float = 0
    exported: float = 0


@dataclass
class AllChargepointData:
    get: AllGet = AllGet()


@dataclass
class AllChargepoints:
    data = AllChargepointData()

    def __init__(self):
        pass

    def no_charge(self):
        """ Wenn keine EV angesteckt sind oder keine Verzögerungen aktiv sind, werden die Algorithmus-Werte
        zurückgesetzt.
        (dient der Robustheit)
        """
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        # Kein EV angesteckt
                        if (not chargepoint.data.get.plug_state or
                                # Kein EV, das Laden soll
                                chargepoint.data.set.charging_ev == -1 or
                                # Kein EV, das auf das Ablaufen der Einschalt- oder Phasenumschaltverzögerung wartet
                                (chargepoint.data.set.charging_ev != -1 and
                                 chargepoint.data.set.charging_ev_data.data["control_parameter"][
                                     "timestamp_perform_phase_switch"] is None and
                                 chargepoint.data.set.charging_ev_data.data["control_parameter"][
                                     "timestamp_auto_phase_switch"] is None and
                                 chargepoint.data.set.charging_ev_data.data["control_parameter"][
                                     "timestamp_switch_on_off"] is None)):
                            continue
                        else:
                            break
                except Exception:
                    log.exception("Fehler in der allgemeinen Ladepunkt-Klasse für Ladepunkt "+cp)
            else:
                data.data.pv_data["all"].reset_pv_data()
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")

    def get_cp_sum(self):
        """ ermittelt die aktuelle Leistung und Zählerstand von allen Ladepunkten.
        """
        imported, exported, power = 0, 0, 0
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        power = power + chargepoint.data.get.power
                        imported = imported + chargepoint.data.get.imported
                        exported = exported + chargepoint.data.get.exported
                except Exception:
                    log.exception("Fehler in der allgemeinen Ladepunkt-Klasse für Ladepunkt "+cp)
            self.data.get.power = power
            Pub().pub("openWB/set/chargepoint/get/power", power)
            self.data.get.imported = imported
            Pub().pub("openWB/set/chargepoint/get/imported", imported)
            self.data.get.exported = exported
            Pub().pub("openWB/set/chargepoint/get/exported", exported)
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")


def empty_dict_factory() -> Dict:
    return {}


def currents_list_factory() -> List[float]:
    return [0.0]*3


def voltages_list_factory() -> List[float]:
    return [230.0]*3


@dataclass
class ConnectedSoc:
    fault_str: str = "Kein Fehler."
    fault_state: int = 0
    range_charged: float = 0
    range_unit: str = "km"
    range: float = 0
    soc: int = 0
    timestamp: Optional[str] = None


@dataclass
class ConnectedSocConfig:
    configured: str = ""


@dataclass
class ConnectedInfo:
    id: int = 0
    name: str = "Ladepunkt"


@dataclass
class ConnectedConfig:
    average_consumption: float = 17
    charge_template: int = 0
    chargemode: str = "stop"
    current_plan: Optional[int] = 0
    ev_template: int = 0
    priority: bool = False


def connected_config_factory() -> ConnectedConfig:
    return ConnectedConfig()


def connected_info_factory() -> ConnectedInfo:
    return ConnectedInfo()


def connected_soc_factory() -> ConnectedSoc:
    return ConnectedSoc()


@dataclass
class ConnectedVehicle:
    config: ConnectedConfig = field(default_factory=connected_config_factory)
    info: ConnectedInfo = field(default_factory=connected_info_factory)
    soc: ConnectedSoc = field(default_factory=connected_soc_factory)
    # soc_config: ConnectedSocConfig = ConnectedSocConfig()


@dataclass
class Log:
    chargemode_log_entry: str = "_"
    imported_at_mode_switch: float = 0
    imported_at_plugtime: float = 0
    imported_since_mode_switch: float = 0
    imported_since_plugged: float = 0
    range_charged: float = 0
    time_charged: str = "00:00"
    timestamp_start_charging: Optional[str] = None


def connected_vehicle_factory() -> ConnectedVehicle:
    return ConnectedVehicle()


@dataclass
class Get:
    charge_state: bool = False
    connected_vehicle: ConnectedVehicle = field(default_factory=connected_vehicle_factory)
    currents: List[float] = field(default_factory=currents_list_factory)
    daily_imported: float = 0
    daily_exported: float = 0
    exported: float = 0
    fault_str: str = "Kein Fehler."
    fault_state: int = 0
    imported: float = 0
    phases_in_use: int = 0
    plug_state: bool = False
    power: float = 0
    rfid_timestamp: Optional[str] = None
    rfid: Optional[str] = None
    state_str: Optional[str] = None
    voltages: List[float] = field(default_factory=voltages_list_factory)


def ev_factory() -> Ev:
    return Ev(0)


def log_factory() -> Log:
    return Log()


@dataclass
class Set:
    autolock_state: int = 0
    change_ev_permitted: bool = False
    charging_ev: int = -1
    charging_ev_prev: int = -1
    current: float = 0
    energy_to_charge: float = 0
    loadmanagement_available: bool = True
    log: Log = field(default_factory=log_factory)
    manual_lock: bool = False
    phases_to_use: int = 0
    plug_time: Optional[str] = None
    required_power: float = 0
    rfid: Optional[str] = None
    charging_ev_data: Ev = field(default_factory=ev_factory)


@dataclass
class Config:
    connection_module: Dict = field(default_factory=empty_dict_factory)
    power_module: Dict = field(default_factory=empty_dict_factory)
    ev: int = 0
    name: str = "Standard-Ladepunkt"
    type: Optional[str] = None
    template: int = 0
    connected_phases: int = 3
    phase_1: int = 0
    auto_phase_switch_hw: bool = False
    control_pilot_interruption_hw: bool = False
    id: int = 0

    def __post_init__(self):
        self.event_update_state: threading.Event

    @property
    def ev(self) -> int:
        return self._ev

    @ev.setter
    def ev(self, ev: int):
        self._ev = ev
        try:
            self.event_update_state.set()
        except AttributeError:
            pass

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get('event_update_state'):
            del state['event_update_state']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


def get_factory() -> Get:
    return Get()


def set_factory() -> Set:
    return Set()


def config_factory() -> Config:
    return Config()


@dataclass
class ChargepointData:
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)
    config: Config = field(default_factory=config_factory)

    def set_event(self, event: Optional[threading.Event] = None) -> None:
        self.event_update_state = event
        if event:
            self.config.event_update_state = event

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        if state.get('event_update_state'):
            del state['event_update_state']
        return state

    def __setstate__(self, state):
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)


class Chargepoint:
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf.
    """

    def __init__(self, index: int, event: Optional[threading.Event]):
        try:
            self.template: CpTemplate = None
            self.chargepoint_module: AbstractChargepoint = None
            self.num = index
            # set current aus dem vorherigen Zyklus, um zu wissen, ob am Ende des Zyklus die Ladung freigegeben wird
            # (für Control-Pilot-Unterbrechung)
            self.set_current_prev = 0
            # bestehende Daten auf dem Broker nicht zurücksetzen, daher nicht publishen
            self.data: ChargepointData = ChargepointData()
            self.data.set_event(event)
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def set_state_and_log(self, message: str) -> None:
        log.info(message)
        self.data.get.state_str = message

    def _is_grid_protection_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob der Netzschutz inaktiv ist oder ob alle Ladepunkt gestoppt werden müssen.
        """
        state = True
        message = None
        general_data = data.data.general_data["general"].data
        if general_data["grid_protection_configured"]:
            if general_data["grid_protection_active"]:
                if general_data["grid_protection_timestamp"] is not None:
                    # Timer ist  abgelaufen
                    if not timecheck.check_timestamp(
                            general_data["grid_protection_timestamp"],
                            general_data["grid_protection_random_stop"]):
                        state = False
                        message = "Ladepunkt gesperrt, da der Netzschutz aktiv ist."
                        Pub().pub("openWB/set/general/grid_protection_timestamp", None)
                        Pub().pub("openWB/set/general/grid_protection_random_stop", 0)
                else:
                    state = False
                    message = "Ladepunkt gesperrt, da der Netzschutz aktiv ist."
        return state, message

    def _is_ripple_control_receiver_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, dass der Rundsteuerempfängerkontakt nicht geschlossen ist.
        """
        state = True
        message = None
        general_data = data.data.general_data["general"].data
        if general_data["ripple_control_receiver"]["configured"]:
            if (general_data["ripple_control_receiver"]["r1_active"] or
                    general_data["ripple_control_receiver"]["r2_active"]):
                state = False
                message = "Ladepunkt gesperrt, da der Rundsteuerempfängerkontakt geschlossen ist."
        return state, message

    def _is_loadmanagement_available(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob Lastmanagement verfügbar ist. Wenn keine Werte vom EVU-Zähler empfangen werden, darf nicht geladen
        werden.
        """
        if self.data.set.loadmanagement_available:
            state = True
            message = None
        else:
            state = False
            message = ("Ladepunkt gesperrt, da keine Werte vom EVU-Zähler empfangen wurden und deshalb kein "
                       "Lastmanagement durchgeführt werden kann. Falls Sie dennoch laden möchten, können Sie als "
                       "EVU-Zähler 'Virtuell' auswählen und einen konstanten Hausverbrauch angeben.")
        return state, message

    def _is_autolock_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob Autolock nicht aktiv ist oder ob die Sperrung durch einen dem LP zugeordneten RFID-Tag aufgehoben
        werden kann.
        """
        message = None
        state = self.template.autolock(
            self.data.set.autolock_state,
            self.data.get.charge_state,
            self.num)
        if not state:
            state = True
        else:
            # Darf Autolock durch Tag überschrieben werden?
            if (data.data.optional_data["optional"].data["rfid"]["active"] and
                    self.template.data["rfid_enabling"]):
                if self.data.get.rfid is None and self.data.set.rfid is None:
                    state = False
                    message = ("Keine Ladung, da der Ladepunkt durch Autolock gesperrt ist und erst per RFID "
                               "freigeschaltet werden muss.")
                else:
                    state = True
                    message = None
            else:
                state = False
                message = "Keine Ladung, da Autolock aktiv ist."
        return state, message

    def _is_manual_lock_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, dass der Ladepunkt nicht manuell gesperrt wurde.
        """
        if (self.data.set.manual_lock is False or
                (self.template.data["rfid_enabling"] and
                    (self.data.get.rfid is not None or self.data.set.rfid is not None))):
            charging_possible = True
            message = None
        else:
            charging_possible = False
            message = "Keine Ladung, da der Ladepunkt manuell gesperrt wurde."
        return charging_possible, message

    def _is_ev_plugged(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob ein EV angesteckt ist
        """
        state = self.data.get.plug_state
        if not state:
            message = "Keine Ladung, da kein Auto angesteckt ist."
        else:
            if self.data.set.plug_time is None:
                self.data.set.plug_time = timecheck.create_timestamp()
                Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/plug_time",
                          self.data.set.plug_time)
            message = None
        return state, message

    def get_state(self) -> Tuple[int, bool, Optional[str]]:
        """prüft alle Bedingungen und ruft die EV-Logik auf.
        Return
        ------
        int : 0..x/ -1
            Nummer des zugeordneten EV / Ladepunkt nicht verfügbar
        message:
            Info-Text des Ladepunkts
        """
        try:
            # Für Control-Pilot-Unterbrechung set current merken.
            self.set_current_prev = self.data.set.current
            self.__validate_rfid()
            message = "Keine Ladung, da ein Fehler aufgetreten ist."
            try:
                charging_possible, message = self._is_grid_protection_inactive()
                if charging_possible:
                    charging_possible, message = self._is_ripple_control_receiver_inactive()
                    if charging_possible:
                        charging_possible, message = self._is_loadmanagement_available()
                        if charging_possible:
                            charging_possible, message = self._is_ev_plugged()
                            if charging_possible:
                                charging_possible, message = self._is_autolock_inactive()
                                if charging_possible:
                                    charging_possible, message = self._is_manual_lock_inactive()
            except Exception:
                log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))
                return -1, False, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()
            if charging_possible:
                num, message_ev = self.template.get_ev(self.data.get.rfid or self.data.set.rfid, self.data.config.ev)
                if message_ev:
                    message = message_ev
                if num != -1:
                    if self.data.get.rfid is not None:
                        self.__link_rfid_to_cp()
                    return num, True, message
                else:
                    self.data.get.state_str = message
            else:
                num = -1
                message_ev = None
            # Charging Ev ist noch das EV des vorherigen Zyklus, wenn das nicht -1 war und jetzt nicht mehr geladen
            # werden soll (-1), Daten zurücksetzen.
            if self.data.set.charging_ev != -1:
                # Altes EV merken
                self.data.set.charging_ev_prev = self.data.set.charging_ev
                Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev_prev",
                          self.data.set.charging_ev_prev)
            if self.data.set.charging_ev_prev != -1:
                # Daten zurücksetzen, wenn nicht geladen werden soll.
                data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)].reset_ev()
                data.data.pv_data["all"].reset_switch_on_off(
                    self, data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)])
                # Abstecken
                if not self.data.get.plug_state:
                    # Standardprofil nach Abstecken laden
                    if data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)].charge_template.data[
                            "load_default"]:
                        self.data.config.ev = 0
                        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/config/ev", 0)
                    # Ladepunkt nach Abstecken sperren
                    if data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)].charge_template.data[
                            "disable_after_unplug"]:
                        self.data.set.manual_lock = True
                        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/manual_lock", True)
                    # Ev wurde noch nicht aktualisiert.
                    chargelog.reset_data(self, data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)])
                    self.data.set.charging_ev_prev = -1
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev_prev",
                              self.data.set.charging_ev_prev)
                    self.data.set.rfid = None
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/rfid", None)
                    self.data.set.plug_time = None
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/plug_time", None)
                    self.data.set.phases_to_use = self.data.get.phases_in_use
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/phases_to_use",
                              self.data.set.phases_to_use)
            self.data.set.charging_ev = -1
            Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev", -1)
            self.data.set.current = 0
            Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/current", 0)
            self.data.set.energy_to_charge = 0
            Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/energy_to_charge", 0)
            return num, False, message
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))
            return -1, False, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def initiate_control_pilot_interruption(self):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data.set.charging_ev_data
            # Unterstützt der Ladepunkt die CP-Unterbrechung und benötigt das Auto eine CP-Unterbrechung?
            if charging_ev.ev_template.data["control_pilot_interruption"]:
                if self.data.config.control_pilot_interruption_hw:
                    # Wird die Ladung gestartet?
                    if self.set_current_prev == 0 and self.data.set.current != 0:
                        cp_interruption.thread_cp_interruption(self.num,
                                                               self.chargepoint_module,
                                                               charging_ev.ev_template.data[
                                                                   "control_pilot_interruption_duration"])
                        message = "Control-Pilot-Unterbrechung für " + str(
                            charging_ev.ev_template.data["control_pilot_interruption_duration"]) + "s."
                        self.set_state_and_log(f"LP {self.num}: {message}")
                else:
                    message = "CP-Unterbrechung nicht möglich, da der Ladepunkt keine CP-Unterbrechung unterstützt."
                    self.set_state_and_log(f"LP {self.num}: {message}")
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def initiate_phase_switch(self):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data.set.charging_ev_data
            # Umschaltung im Gange
            if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] is not None:
                phase_switch_pause = charging_ev.ev_template.data["phase_switch_pause"]
                # Umschaltung abgeschlossen
                if not timecheck.check_timestamp(
                        charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"],
                        6 + phase_switch_pause - 1):
                    log.debug("phase switch running")
                    charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] = None
                    Pub().pub("openWB/set/vehicle/" + str(charging_ev.num) +
                              "/control_parameter/timestamp_perform_phase_switch", None)
                    # Aktuelle Ladeleistung und Differenz wieder freigeben.
                    if charging_ev.data["control_parameter"]["phases"] == 3:
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= charging_ev.data[
                            "control_parameter"]["required_current"] * 3 * 230
                    elif charging_ev.data["control_parameter"]["phases"] == 1:
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= charging_ev.ev_template.data[
                            "max_current_one_phase"] * 230
                    self.data.set.current = charging_ev.data["control_parameter"]["required_current"]
                else:
                    # Wenn eine Umschaltung im Gange ist, muss erst gewartet werden, bis diese fertig ist.
                    if self.data.set.phases_to_use == 3:
                        message = "Umschaltung von 1 auf 3 Phasen."
                    elif self.data.set.phases_to_use == 1:
                        message = "Umschaltung von 3 auf 1 Phase."
                    else:
                        raise ValueError(str(self.data.set.phases_to_use)+" ist keine gültige Phasenzahl (1/3).")
                    self.data.get.state_str = message
                return
            # Wenn noch kein Eintrag im Protokoll erstellt wurde, wurde noch nicht geladen und die Phase kann noch
            # umgeschaltet werden.
            if (not charging_ev.ev_template.data["prevent_phase_switch"] or
                    self.data.set.log.imported_since_plugged == 0):
                # Einmal muss die Anzahl der Phasen gesetzt werden.
                if self.data.set.phases_to_use == 0:
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/phases_to_use",
                              charging_ev.data["control_parameter"]["phases"])
                    self.data.set.phases_to_use = charging_ev.data["control_parameter"]["phases"]
                # Manche EVs brauchen nach der Umschaltung mehrere Zyklen, bis sie mit den drei Phasen laden. Dann darf
                # nicht zwischendurch eine neue Umschaltung getriggert werden.
                if self.data.set.phases_to_use != charging_ev.data["control_parameter"]["phases"]:
                    # Wenn die Umschaltverzögerung aktiv ist, darf nicht umgeschaltet werden.
                    if charging_ev.data["control_parameter"]["timestamp_auto_phase_switch"] is None:
                        if self.data.config.auto_phase_switch_hw:
                            charge_state = self.data.get.charge_state
                            phase_switch.thread_phase_switch(
                                self.num, self.chargepoint_module, charging_ev.data["control_parameter"]["phases"],
                                charging_ev.ev_template.data["phase_switch_pause"],
                                charge_state)
                            log.debug("start phase switch phases_to_use " +
                                      str(self.data.set.phases_to_use) +
                                      "control_parameter phases " +
                                      str(charging_ev.data["control_parameter"]["phases"]))
                            # 1 -> 3
                            if charging_ev.data["control_parameter"]["phases"] == 3:
                                message = "Umschaltung von 1 auf 3 Phasen."
                                # Timestamp für die Durchführungsdauer
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] += charging_ev.data[
                                    "control_parameter"]["required_current"] * 3 * 230
                                charging_ev.data["control_parameter"][
                                    "timestamp_perform_phase_switch"] = timecheck.create_timestamp()
                                Pub().pub("openWB/set/vehicle/"+str(charging_ev.num) +
                                          "/control_parameter/timestamp_perform_phase_switch",
                                          charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"])
                            else:
                                message = "Umschaltung von 3 auf 1 Phase."
                                # Timestamp für die Durchführungsdauer
                                charging_ev.data["control_parameter"][
                                    "timestamp_perform_phase_switch"] = timecheck.create_timestamp()
                                Pub().pub("openWB/set/vehicle/"+str(charging_ev.num) +
                                          "/control_parameter/timestamp_perform_phase_switch",
                                          charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"])
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                data.data.pv_data["all"].data["set"][
                                    "reserved_evu_overhang"] += charging_ev.ev_template.data[
                                        "max_current_one_phase"] * 230
                            self.set_state_and_log(f"LP {self.num}: {message}")
                            if self.data.set.phases_to_use != charging_ev.data["control_parameter"]["phases"]:
                                Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/phases_to_use",
                                          charging_ev.data["control_parameter"]["phases"])
                                self.data.set.phases_to_use = charging_ev.data["control_parameter"]["phases"]
                        else:
                            log.error(
                                "Phasenumschaltung an Ladepunkt" + str(self.num) +
                                " nicht möglich, da der Ladepunkt keine Phasenumschaltung unterstützt.")
                    else:
                        log.error("Phasenumschaltung an Ladepunkt" + str(self.num) +
                                  " nicht möglich, da gerade eine Umschaltung im Gange ist.")

        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def get_phases(self) -> int:
        """ ermittelt die maximal mögliche Anzahl Phasen, die von Konfiguration, Auto und Ladepunkt unterstützt wird
        und prüft anschließend, ob sich die Anzahl der genutzten Phasen geändert hat.
        """
        phases = 0
        charging_ev = self.data.set.charging_ev_data
        mode = charging_ev.charge_template.data["chargemode"]["selected"]
        config = self.data.config
        if charging_ev.ev_template.data["max_phases"] <= config.connected_phases:
            phases = charging_ev.ev_template.data["max_phases"]
            log.debug(f"EV-Phasenzahl beschränkt die nutzbaren Phasen auf {phases}")
        else:
            phases = config.connected_phases
            log.debug(f"Anzahl angeschlossener Phasen beschränkt die nutzbaren Phasen auf {phases}")

        chargemode_phases = data.data.general_data["general"].get_phases_chargemode(mode)
        # Wenn die Lademodus-Phasen 0 sind, wird die bisher genutzte Phasenzahl weiter genutzt,
        # bis der Algorithmus eine Umschaltung vorgibt, zB weil der gewählte Lademodus eine
        # andere Phasenzahl benötigt oder bei PV-Laden die automatische Umschaltung aktiv ist.
        if chargemode_phases == 0:
            if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] is None:
                if self.data.get.charge_state:
                    phases = self.data.set.phases_to_use
                else:
                    if ((not charging_ev.ev_template.data["prevent_phase_switch"] or
                            self.data.set.log.imported_since_plugged == 0) and
                            self.data.config.auto_phase_switch_hw):
                        phases = 1
                    else:
                        log.debug(("Automat. Phasenumschaltung vor Ladestart: Es wird die kleinstmögliche Phasenzahl "
                                   f"angenommen. Phasenzahl: {phases}"))
            else:
                phases = charging_ev.data["control_parameter"]["phases"]
                log.debug(f"Umschaltung wird durchgeführt, Phasenzahl nicht ändern {phases}")
        elif chargemode_phases < phases:
            phases = chargemode_phases
            log.debug(f"Lademodus-Phasen beschränkt die nutzbaren Phasen auf {phases}")

        if phases != self.data.get.phases_in_use:
            # Wenn noch kein Eintrag im Protokoll erstellt wurde, wurde noch nicht geladen und die Phase kann noch
            # umgeschaltet werden.
            if self.data.set.log.imported_since_plugged != 0:
                if charging_ev.ev_template.data["prevent_phase_switch"]:
                    log.info(f"Phasenumschaltung an Ladepunkt {self.num} nicht möglich, da bei EV"
                             f"{charging_ev.num} nach Ladestart nicht mehr umgeschaltet werden darf.")
                    phases = self.data.get.phases_in_use
                elif self.data.config.auto_phase_switch_hw is False:
                    log.info(f"Phasenumschaltung an Ladepunkt {self.num} wird durch die Hardware nicht unterstützt.")
                    phases = self.data.get.phases_in_use
        if phases != charging_ev.data["control_parameter"]["phases"]:
            charging_ev.data["control_parameter"]["phases"] = phases
            Pub().pub("openWB/set/vehicle/"+str(charging_ev.num)+"/control_parameter/phases", phases)
        return phases

    def __link_rfid_to_cp(self) -> None:
        """ Wenn der Tag einem EV zugeordnet worden ist, wird der Tag unter set/rfid abgelegt und muss der Timer
        zurückgesetzt werden.
        """
        rfid = self.data.get.rfid
        self.data.set.rfid = rfid
        Pub().pub("openWB/chargepoint/"+str(self.num)+"/set/rfid", rfid)
        self.data.get.rfid = None
        Pub().pub("openWB/chargepoint/"+str(self.num)+"/get/rfid", None)
        self.chargepoint_module.clear_rfid()
        self.data.get.rfid_timestamp = None
        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)

    def __validate_rfid(self) -> None:
        """Prüft, dass der Tag an diesem Ladepunkt gültig ist und  dass dieser innerhalb von 5 Minuten einem EV
        zugeordnet wird.
        """
        msg = ""
        if self.data.get.rfid is not None:
            if data.data.optional_data["optional"].data["rfid"]["active"]:
                rfid = self.data.get.rfid
                if rfid in self.template.data["valid_tags"] or len(self.template.data["valid_tags"]) == 0:
                    if self.data.get.rfid_timestamp is None:
                        self.data.get.rfid_timestamp = timecheck.create_timestamp()
                        Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp",
                                  self.data.get.rfid_timestamp)
                        return
                    else:
                        if timecheck.check_timestamp(self.data.get.rfid_timestamp, 300):
                            return
                        else:
                            self.data.get.rfid_timestamp = None
                            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid_timestamp", None)
                            msg = "Es ist in den letzten 5 Minuten kein EV angesteckt worden, dem " \
                                f"der RFID-Tag/Code {rfid} zugeordnet werden kann. Daher wird dieser verworfen."
                else:
                    msg = f"Der Tag {rfid} ist an Ladepunkt {self.num} nicht gültig."
            else:
                msg = "RFID ist nicht aktiviert."
            self.data.get.rfid = None
            Pub().pub(f"openWB/set/chargepoint/{self.num}/get/rfid", None)
            self.chargepoint_module.clear_rfid()
            self.set_state_and_log(f"LP{self.num}: {msg}")

    def update(self, ev_list:  Dict[str, Ev]) -> None:
        vehicle, charging_possible, message = self.get_state()
        if vehicle != -1:
            try:
                charging_ev = self._get_charging_ev(vehicle, ev_list)
                phases = self.get_phases()
                state, message_ev, submode, required_current = charging_ev.get_required_current(
                    self.data.set.log.imported_since_mode_switch)
                self._pub_connected_vehicle(charging_ev)
                # Einhaltung des Minimal- und Maximalstroms prüfen
                required_current = charging_ev.check_min_max_current(
                    required_current, charging_ev.data["control_parameter"]["phases"])
                current_changed, mode_changed = charging_ev.check_state(
                    required_current, self.data.set.current, self.data.get.charge_state)

                # Die benötigte Stromstärke hat sich durch eine Änderung des Lademodus oder der
                # Konfiguration geändert. Die Zuteilung entsprechend der Priorisierung muss neu geprüft
                # werden. Daher muss der LP zurückgesetzt werden, wenn er gerade lädt, um in der Regelung
                # wieder berücksichtigt zu werden.
                if current_changed:
                    log.debug(f"LP{self.num}: Da sich die Stromstärke geändert hat, muss der Ladepunkt im "
                              "Algorithmus neu priorisiert werden.")
                    data.data.pv_data["all"].reset_switch_on_off(
                        self, charging_ev)
                    charging_ev.reset_phase_switch()
                    min_charge_current = self.data.set.current - \
                        charging_ev.ev_template.data["nominal_difference"]
                    if max(self.data.get.currents) > min_charge_current:
                        self.data.set.current = 0
                    else:
                        # Wenn nicht geladen wird, obwohl geladen werde kann, soll das EV im Algorithmus
                        # nicht berücksichtigt werden. Wenn der Soll-Strom gesetzt ist, wird das EV nur im
                        # LM berücksichtigt.
                        self.data.set.current = required_current
                    # Da nicht bekannt ist, ob mit Bezug, Überschuss oder aus dem Speicher geladen wird,
                    # wird die freiwerdende Leistung erst im nächsten Durchlauf berücksichtigt. Ggf.
                    # entsteht so eine kurze Unterbrechung der Ladung, wenn während dem Laden
                    # umkonfiguriert wird.
                if charging_possible:
                    message = message_ev if message_ev else message
                    charging_ev.set_control_parameter(submode, required_current)
                # Ein Eintrag muss nur erstellt werden, wenn vorher schon geladen wurde und auch danach noch
                # geladen werden soll.
                if mode_changed and self.data.get.charge_state and state:
                    chargelog.save_data(self, charging_ev)

                # Wenn die Nachrichten gesendet wurden, EV wieder löschen, wenn das EV im Algorithmus nicht
                # berücksichtigt werden soll.
                if not state:
                    if self.data.set.charging_ev != -1:
                        # Altes EV merken
                        self.data.set.charging_ev_prev = self.data.set.charging_ev
                        Pub().pub("openWB/set/chargepoint/"+str(self.num) +
                                  "/set/charging_ev_prev", self.data.set.charging_ev_prev)
                    self.data.set.charging_ev = -1
                    Pub().pub("openWB/set/chargepoint/" +
                              str(self.num)+"/set/charging_ev", -1)
                    log.debug(f'LP {self.num}, EV: {self.data.set.charging_ev_data.data["name"]}'
                              f' (EV-Nr.{vehicle}): Lademodus '
                              f'{charging_ev.charge_template.data["chargemode"]["selected"]}, Submodus: '
                              f'{charging_ev.data["control_parameter"]["submode"]}')
                else:
                    if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] is not None and
                            not self.data.get.charge_state and
                            data.data.pv_data["all"].data["set"]["overhang_power_left"] == 0):
                        log.error("Reservierte Leistung kann nicht 0 sein.")

                    log.debug(
                        "LP " + str(self.num) + ", EV: " + self.data.set.charging_ev_data.data
                        ["name"] + " (EV-Nr." + str(vehicle) + "): Theoretisch benötigter Strom " +
                        str(required_current) + "A, Lademodus " +
                        str(charging_ev.charge_template.data["chargemode"]["selected"]) + ", Submodus: " +
                        str(charging_ev.data["control_parameter"]["submode"]) + ", Phasen: " + str(phases) +
                        ", Priorität: " + str(charging_ev.charge_template.data["prio"]) +
                        ", max. Ist-Strom: " + str(max(self.data.get.currents)))
            except Exception:
                log.exception("Fehler im Prepare-Modul für Ladepunkt "+str(self.num))
                ev_list[f"ev{vehicle}"].data["control_parameter"]["submode"] = "stop"
        else:
            # Wenn kein EV zur Ladung zugeordnet wird, auf hinterlegtes EV zurückgreifen.
            self._pub_connected_vehicle(
                ev_list["ev"+str(self.data.config.ev)])
        if message is not None and self.data.get.state_str is None:
            self.set_state_and_log(f"LP {self.num}: {message}")

    def _get_charging_ev(self, vehicle: int, ev_list: Dict[str, Ev]) -> Ev:
        charging_ev = ev_list[f"ev{vehicle}"]
        # Das EV darf nur gewechselt werden, wenn noch nicht geladen wurde.
        if (self.data.set.charging_ev == vehicle or
                self.data.set.charging_ev_prev == vehicle):
            # Das EV entspricht dem bisherigen EV.
            self.data.set.charging_ev = vehicle
            Pub().pub("openWB/set/chargepoint/" +
                      str(self.num)+"/set/charging_ev", vehicle)
            charging_ev.ev_template.data = charging_ev.data["set"]["ev_template"]
            self.data.set.charging_ev_data = charging_ev
            Pub().pub("openWB/set/chargepoint/"+str(self.num) +
                      "/set/change_ev_permitted", [True, ""])
        else:
            # Darf das EV geändert werden?
            if (self.data.set.log.imported_at_plugtime == 0 or
                    self.data.set.log.imported_at_plugtime == self.data.get.imported):
                self.data.set.charging_ev = vehicle
                Pub().pub("openWB/set/chargepoint/" +
                          str(self.num)+"/set/charging_ev", vehicle)
                self.data.set.charging_ev_data = charging_ev
                Pub().pub("openWB/set/chargepoint/"+str(self.num) +
                          "/set/change_ev_permitted", [True, ""])
                charging_ev.data["set"]["ev_template"] = charging_ev.ev_template.data
                Pub().pub("openWB/set/vehicle/"+str(charging_ev.num) +
                          "/set/ev_template", charging_ev.data["set"]["ev_template"])
            else:
                # Altes EV beibehalten.
                if self.data.set.charging_ev != -1:
                    vehicle = self.data.set.charging_ev
                elif self.data.set.charging_ev_prev != -1:
                    vehicle = self.data.set.charging_ev_prev
                    self.data.set.charging_ev = vehicle
                    Pub().pub(
                        "openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev", vehicle)
                    self.data.set.charging_ev_prev = -1
                    Pub().pub(
                        "openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev_prev", -1)
                else:
                    raise ValueError(
                        "Wenn kein aktuelles und kein vorheriges Ev zugeordnet waren, \
                            sollte noch nicht geladen worden sein.")
                charging_ev = ev_list["ev" + str(vehicle)]
                charging_ev.ev_template.data = charging_ev.data["set"]["ev_template"]
                self.data.set.charging_ev_data = charging_ev
                Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/change_ev_permitted", [
                    False, "Das Fahrzeug darf nur geändert werden, wenn noch nicht geladen wurde. \
                            Bitte abstecken, dann wird das gewählte Fahrzeug verwendet."])
                log.warning(
                    "Das Fahrzeug darf nur geändert werden, wenn noch nicht geladen wurde.")
        return charging_ev

    def _pub_connected_vehicle(self, vehicle):
        """ published die Daten, die zur Anzeige auf der Hauptseite benötigt werden.

        Parameter
        ---------
        vehicle: dict
            EV, das dem LP zugeordnet ist
        cp_num: int
            LP-Nummer
        """
        try:
            # soc_config_obj = {
            #     # "configured": vehicle.data["soc"]["config"]["configured"],
            #     # "manual": vehicle.data["soc"]["config"]["manual"]
            # }
            soc_obj = ConnectedSoc(
                range_charged=self.data.set.log.range_charged,
                range_unit=data.data.general_data["general"].data["range_unit"],
            )
            if vehicle.data["get"].get("soc_timestamp"):
                soc_obj.timestamp = vehicle.data["get"]["soc_timestamp"]
                soc_obj.soc = vehicle.data["get"]["soc"]
                soc_obj.fault_state = vehicle.data["get"]["fault_state"]
                soc_obj.fault_str = vehicle.data["get"]["fault_str"]
            if vehicle.data["get"].get("range"):
                soc_obj.range = vehicle.data["get"]["range"]
            info_obj = ConnectedInfo(id=vehicle.num,
                                     name=vehicle.data["name"])
            if (vehicle.charge_template.data["chargemode"]["selected"] == "time_charging" or
                    vehicle.charge_template.data["chargemode"]["selected"] == "scheduled_charging"):
                current_plan = vehicle.data["control_parameter"]["current_plan"]
            else:
                current_plan = None
            config_obj = ConnectedConfig(charge_template=vehicle.charge_template.ct_num,
                                         ev_template=vehicle.ev_template.et_num,
                                         chargemode=vehicle.charge_template.data["chargemode"]["selected"],
                                         priority=vehicle.charge_template.data["prio"],
                                         current_plan=current_plan,
                                         average_consumption=vehicle.ev_template.data["average_consump"])
            # if soc_config_obj != self.data.get.connected_vehicle.soc_config:
            #     Pub().pub("openWB/chargepoint/"+str(self.cp_num) +
            #               "/get/connected_vehicle/soc_config", soc_config_obj)
            if soc_obj != self.data.get.connected_vehicle.soc:
                Pub().pub("openWB/chargepoint/"+str(self.num) +
                          "/get/connected_vehicle/soc", dataclasses.asdict(soc_obj))
            if info_obj != self.data.get.connected_vehicle.info:
                Pub().pub("openWB/chargepoint/"+str(self.num) +
                          "/get/connected_vehicle/info", dataclasses.asdict(info_obj))
            if config_obj != self.data.get.connected_vehicle.config:
                Pub().pub("openWB/chargepoint/"+str(self.num) +
                          "/get/connected_vehicle/config", dataclasses.asdict(config_obj))
        except Exception:
            log.exception("Fehler im Prepare-Modul")


def get_chargepoint_template_default():
    return {
        "name": "Standard Ladepunkt-Vorlage",
        "autolock": {
            "wait_for_charging_end": False,
            "active": False
        },
        "rfid_enabling": False,
        "valid_tags": []
    }


def get_autolock_plan_default():
    return {
        "name": "Standard Autolock-Plan",
        "frequency": {
            "selected": "daily",
            "once": ["2021-11-01", "2021-11-05"],
            "weekly": [False, False, False, False, False, False, False]
        },
        "time": ["07:00", "16:00"],
        "active": False
    }


class CpTemplate:
    """ Vorlage für einen Ladepunkt.
    """

    def __init__(self):
        self.data = {"autolock": {"plans": {}}}

    def autolock(self, autolock_state, charge_state, num):
        """ ermittelt den Status des Autolock und published diesen.

        Parameter
        ---------
        autolock_state : int
            Autolock-Status-Code:
            0 = standby
            1 = Nach Beenden der Ladung wird Autolock aktiviert
            2 = durch Autolock gesperrt
            3 = nicht durch Autolock gesperrt
            4 = Autolock manuell deaktiviert

        charge_state : int
            Ladung aktiv/nicht aktiv

        num : str
            Ladepunkt-Nummer

        Return
        ------
        False: nicht durch Autolock gesperrt -> Ladung möglich
        True: durch Autolock gesperrt
        """
        try:
            if (self.data["autolock"]["active"]):
                if self.data["autolock"]["plans"]:
                    if autolock_state != 4:
                        if timecheck.check_plans_timeframe(
                                self.data["autolock"]["plans"]) is not None:
                            if self.data["autolock"]["wait_for_charging_end"]:
                                if charge_state:
                                    state = 1
                                else:
                                    state = 2
                            else:
                                state = 2
                        else:
                            state = 3

                        Pub().pub(
                            "openWB/set/chargepoint/" + str(num) +
                            "/set/autolock_state", state)
                        if (state == 1) or (state == 3):
                            return False
                        elif state == 2:
                            return True
                    else:
                        return False
                else:
                    log.info("Keine Sperrung durch Autolock, weil keine Zeitpläne konfiguriert sind.")
                    return False
            else:
                return False
        except Exception:
            log.exception(
                "Fehler in der Ladepunkt-Template Klasse von " + str(num))
            return False

    def autolock_manual_disabling(self, topic_path):
        """ aktuelles Autolock wird außer Kraft gesetzt.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"]):
                Pub().pub(topic_path + "/get/autolock", 4)
        except Exception:
            log.exception(
                "Fehler in der Ladepunkt-Template Klasse")

    def autolock_manual_enabling(self, topic_path):
        """ aktuelles Autolock wird wieder aktiviert.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"]):
                Pub().pub(topic_path + "/get/autolock", 0)
        except Exception:
            log.exception(
                "Fehler in der Ladepunkt-Template Klasse")

    def autolock_enable_after_charging_end(self, autolock_state, topic_path):
        """Wenn kein Strom für den Ladepunkt übrig ist, muss Autolock ggf noch aktiviert werden.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"]) and autolock_state == 1:
                Pub().pub(topic_path + "/set/autolock", 2)
        except Exception:
            log.exception(
                "Fehler in der Ladepunkt-Template Klasse")

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
            if data.data.optional_data["optional"].data["rfid"]["active"] and rfid is not None:
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


class ChargepointStateUpdate:
    def __init__(self,
                 index: int,
                 event_copy_data: threading.Event,
                 event_global_data_initialized: threading.Event,
                 cp_template_data: Dict,
                 ev_data: Dict,
                 ev_charge_template_data: Dict,
                 ev_template_data: Dict) -> None:
        self.event_update_state = threading.Event()
        self.event_copy_data = event_copy_data
        self.event_global_data_initialized = event_global_data_initialized
        self.chargepoint: Chargepoint = Chargepoint(index, self.event_update_state)
        self.cp_template_data = cp_template_data
        self.ev_data = ev_data
        self.ev_charge_template_data = ev_charge_template_data
        self.ev_template_data = ev_template_data
        Thread(target=self.update, args=()).start()

    def update(self):
        self.event_global_data_initialized.wait()
        while self.event_update_state.wait():
            try:
                self.event_copy_data.clear()
                cp = copy.deepcopy(self.chargepoint)
                cp.template = copy.deepcopy(self.cp_template_data[f"cpt{self.chargepoint.data.config.template}"])
                ev_list = {}
                for ev in self.ev_data:
                    if "name" in self.ev_data[ev].data:
                        ev_list[ev] = copy.deepcopy(self.ev_data[ev])
                for vehicle in ev_list:
                    try:
                        # Globaler oder individueller Lademodus?
                        if data.data.general_data["general"].data["chargemode_config"]["individual_mode"]:
                            ev_list[vehicle].charge_template = copy.deepcopy(self.ev_charge_template_data["ct" + str(
                                ev_list[vehicle].data["charge_template"])])
                        else:
                            ev_list[vehicle].charge_template = copy.deepcopy(self.ev_charge_template_data["ct0"])
                        # zuerst das aktuelle Template laden
                        ev_list[vehicle].ev_template = copy.deepcopy(self.ev_template_data["et" + str(
                            ev_list[vehicle].data["ev_template"])])
                    except Exception:
                        log.exception("Fehler im Prepare-Modul für EV "+str(vehicle))
                self.event_copy_data.set()
                cp.update(ev_list)
                self.event_update_state.clear()
            except Exception:
                log.exception("Fehler ChargepointStateUpdate")
                self.event_copy_data.set()
                self.event_update_state.clear()
