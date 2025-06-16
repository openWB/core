"""Ladepunkt-Logik

charging_ev: EV, das aktuell laden darf
charging_ev_prev: EV, das vorher geladen hat. Dies wird benötigt, da wenn das EV nicht mehr laden darf, z.B. weil
Autolock aktiv ist, gewartet werden muss, bis die Ladeleistung 0 ist und dann erst der Eintrag im Protokoll erstellt
werden kann.
charging_ev = -1 zeigt an, dass der LP im Algorithmus nicht berücksichtigt werden soll. Ist das Ev abgesteckt, wird
auch charging_ev_prev -1 und im nächsten Zyklus kann ein neues Profil geladen werden.

ID-Tag/Code-Eingabe:
Mit einem ID-Tag/Code kann optional der Ladepunkt freigeschaltet werden, es wird gleichzeitig immer ein EV damit
zugeordnet, mit dem nach der Freischaltung geladen werden soll. Wenn max 5 Min nach dem Scannen kein Auto
angesteckt wird, wird der Tag verworfen. Ebenso wenn kein EV gefunden wird.
Tag-Liste: Tags, mit denen der Ladepunkt freigeschaltet werden kann. Ist diese leer, kann mit jedem Tag der Ladepunkt
freigeschaltet werden.
"""
from dataclasses import asdict
import dataclasses
import logging
from threading import Thread, Event
import traceback
from typing import Dict, Optional, Tuple

from control.algorithm.utils import get_medium_charging_current
from control.chargelog import chargelog
from control import data
from control.chargemode import Chargemode
from control.chargepoint.chargepoint_data import ChargepointData, ConnectedConfig, ConnectedInfo, ConnectedSoc, Get, Log
from control.chargepoint.chargepoint_template import CpTemplate
from control.chargepoint.control_parameter import control_parameter_factory
from control.chargepoint.charging_type import ChargingType
from control.chargepoint.rfid import ChargepointRfidMixin
from control.ev.charge_template import ChargeTemplate
from control.ev.ev import Ev
from control import phase_switch
from control.chargepoint.chargepoint_state import CHARGING_STATES, ChargepointState
from helpermodules.broker import BrokerClient
from helpermodules.phase_mapping import convert_single_evu_phase_to_cp_phase
from helpermodules.pub import Pub
from helpermodules import timecheck
from helpermodules.utils import thread_handler
from modules.common.abstract_chargepoint import AbstractChargepoint
from helpermodules.timecheck import check_timestamp, create_timestamp


def get_chargepoint_config_default() -> dict:
    return {
        "name": "neuer Ladepunkt",
        "type": None,
        "ev": 0,
        "template": 0,
        "connected_phases": 3,
        "phase_1": 1,
        "auto_phase_switch_hw": False,
        "control_pilot_interruption_hw": False
    }


def get_chargepoint_get_default() -> Dict:
    return asdict(Get)


log = logging.getLogger(__name__)


class Chargepoint(ChargepointRfidMixin):
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf.
    """
    MAX_FAILED_PHASE_SWITCHES = 2

    def __init__(self, index: int, event: Optional[Event]):
        try:
            self.template: CpTemplate = None
            self.chargepoint_module: AbstractChargepoint = None
            self.num = index
            self.chargemode_changed = False
            self.submode_changed = False
            # bestehende Daten auf dem Broker nicht zurücksetzen, daher nicht veröffentlichen
            self.data: ChargepointData = ChargepointData()
            self.data.set_event(event)
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def set_state_and_log(self, message: str) -> None:
        if message:
            log.info(f"LP {self.num}: {message}")
            if self.data.get.state_str is None:
                self.data.get.state_str = message
            elif message not in self.data.get.state_str:
                self.data.get.state_str += f" {message}"

    def _is_grid_protection_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob der Netzschutz inaktiv ist oder ob alle Ladepunkt gestoppt werden müssen.
        """
        state = True
        message = None
        general_data = data.data.general_data.data
        if general_data.grid_protection_configured:
            if general_data.grid_protection_active:
                if general_data.grid_protection_timestamp is not None:
                    # Timer ist  abgelaufen
                    if not timecheck.check_timestamp(
                            general_data.grid_protection_timestamp,
                            general_data.grid_protection_random_stop):
                        state = False
                        message = "Ladepunkt gesperrt, da der Netzschutz aktiv ist."
                        general_data.grid_protection_timestamp = None
                        general_data.grid_protection_random_stop = 0
                else:
                    state = False
                    message = "Ladepunkt gesperrt, da der Netzschutz aktiv ist."
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
            message = ("Ladepunkt gesperrt, da keine Werte vom EVU- oder Zwischenzähler-Zähler empfangen wurden und "
                       "deshalb kein Lastmanagement durchgeführt werden kann. Bitte schaue auf der Status-Seite nach "
                       "Fehlermeldungen bei den Zählern. Falls Du dennoch laden möchtest, kannst Du als "
                       "Gerät 'Virtuelles Gerät' mit einer Komponente 'Virtueller Zähler' verwenden.")
        return state, message

    def _is_autolock_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob Autolock nicht aktiv ist oder ob die Sperrung durch einen dem LP zugeordneten ID-Tag aufgehoben
        werden kann.
        """
        message = None
        state = self.template.is_locked_by_autolock(self.data.get.charge_state)
        if not state:
            state = True
        else:
            # Darf Autolock durch Tag überschrieben werden?
            if data.data.optional_data.data.rfid.active:
                if self.data.get.rfid is None and self.data.set.rfid is None:
                    state = False
                    message = ("Keine Ladung, da der Ladepunkt durch Sperren nach Uhrzeit gesperrt ist und erst "
                               "per ID-Tag freigeschaltet werden muss.")
                else:
                    state = True
                    message = None
            else:
                state = False
                message = "Keine Ladung, da Sperren nach Uhrzeit aktiv ist."
        return state, message

    def _is_manual_lock_inactive(self) -> Tuple[bool, Optional[str]]:
        # Die Pro schickt je nach Timing auch nach Abstecken noch ein paar Zyklen den Tag. Dann darf der Ladepunkt
        # nicht wieder entsperrt werden.
        if (self.data.get.rfid or
            self.data.get.vehicle_id or
                self.data.set.rfid) in self.template.data.valid_tags:
            Pub().pub(f"openWB/set/chargepoint/{self.num}/set/manual_lock", False)
        elif self.template.data.disable_after_unplug and self.data.get.plug_state is False:
            Pub().pub(f"openWB/set/chargepoint/{self.num}/set/manual_lock", True)

        if self.data.set.manual_lock:
            charging_possible = False
            message = "Keine Ladung, da der Ladepunkt gesperrt ist."
        else:
            charging_possible = True
            message = None
        return charging_possible, message

    def _is_ev_plugged(self) -> Tuple[bool, Optional[str]]:
        state = self.data.get.plug_state
        if not state:
            message = "Keine Ladung, da kein Auto angesteckt ist."
        else:
            message = None
        return state, message

    def is_charging_possible(self) -> Tuple[bool, Optional[str]]:
        message = "Keine Ladung, da ein Fehler aufgetreten ist."
        try:
            charging_possible, message = self._is_grid_protection_inactive()
            if charging_possible:
                charging_possible, message = self._is_loadmanagement_available()
                if charging_possible:
                    charging_possible, message = self._is_manual_lock_inactive()
                    if charging_possible:
                        charging_possible, message = self._is_ev_plugged()
                        if charging_possible:
                            charging_possible, message = self._is_autolock_inactive()
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))
            return False, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()
        return charging_possible, message

    def _process_charge_stop(self) -> None:
        # Charging Ev ist noch das EV des vorherigen Zyklus, wenn das nicht -1 war und jetzt nicht mehr geladen
        # werden soll (-1), Daten zurücksetzen.
        # Ocpp Stop Funktion aufrufen
        if not self.data.get.plug_state and self.data.set.ocpp_transaction_id is not None:
            data.data.optional_data.stop_transaction(
                self.data.config.ocpp_chargebox_id,
                self.chargepoint_module.fault_state,
                self.data.get.imported,
                self.data.set.ocpp_transaction_id,
                self.data.set.rfid)
            Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/ocpp_transaction_id", None)
        if self.data.set.charging_ev_prev != -1:
            # Daten zurücksetzen, wenn nicht geladen werden soll.
            self.reset_control_parameter_at_charge_stop()
            data.data.counter_all_data.get_evu_counter().reset_switch_on_off(
                self, data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)])
            # Abstecken
            if not self.data.get.plug_state:
                self.data.control_parameter = control_parameter_factory()
                # Standardprofil nach Abstecken laden
                if self.data.set.charge_template.data.load_default:
                    self.data.config.ev = 0
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/config/ev", 0)
                # Ladepunkt nach Abstecken sperren
                if self.template.data.disable_after_unplug:
                    self.data.set.manual_lock = True
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/manual_lock", True)
                    log.debug("/set/manual_lock True")
                # Ev wurde noch nicht aktualisiert.
                # Ladeprofil aus den Einstellungen laden.
                self.update_charge_template(data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)].charge_template)
                chargelog.save_and_reset_data(self, data.data.ev_data["ev"+str(self.data.set.charging_ev_prev)])
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

    def setup_values_at_start(self):
        self._reset_values_at_start()
        self._set_values_at_start()

    def set_control_parameter(self, submode: str, required_current: float):
        """ setzt die Regel-Parameter, die der Algorithmus verwendet.

        Parameter
        ---------
        submode: str
            neuer Lademodus, in dem geladen werden soll
        """
        try:
            self.data.control_parameter.submode = Chargemode(submode)
            if submode == "time_charging":
                self.data.control_parameter.chargemode = Chargemode.TIME_CHARGING
            else:
                self.data.control_parameter.chargemode = Chargemode(
                    self.data.set.charge_template.data.chargemode.selected)
            self.data.control_parameter.prio = self.data.set.charge_template.data.prio
            self.data.control_parameter.required_current = required_current
            if self.template.data.charging_type == ChargingType.AC.value:
                self.data.control_parameter.min_current = self.data.set.charging_ev_data.ev_template.data.min_current
            else:
                self.data.control_parameter.min_current = self.data.set.charging_ev_data.ev_template.data.dc_min_current
        except Exception:
            log.exception("Fehler im LP-Modul "+str(self.num))

    def _reset_values_at_start(self):
        self.data.set.loadmanagement_available = True

    def _set_values_at_start(self):
        if self.data.get.plug_state and self.data.set.plug_time is None:
            self.data.set.plug_time = timecheck.create_timestamp()
            Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/plug_time",
                      self.data.set.plug_time)

    def remember_previous_values(self):
        self.data.set.charge_state_prev = self.data.get.charge_state
        self.data.set.plug_state_prev = self.data.get.plug_state
        self.data.set.current_prev = self.data.set.current
        self.data.set.ev_prev = self.data.config.ev
        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/charge_state_prev", self.data.set.charge_state_prev)
        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/plug_state_prev", self.data.set.plug_state_prev)
        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/current_prev", self.data.set.current_prev)
        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/ev_prev", self.data.set.ev_prev)

    def reset_log_data_chargemode_switch(self) -> None:
        reset_log = Log()
        # Wenn ein Zwischeneintrag, zB bei Wechsel des Lademodus, erstellt wird, Zählerstände nicht verwerfen.
        reset_log.imported_at_mode_switch = self.data.get.imported
        reset_log.imported_at_plugtime = self.data.set.log.imported_at_plugtime
        reset_log.imported_since_plugged = self.data.set.log.imported_since_plugged
        self.data.set.log = reset_log
        Pub().pub(f"openWB/set/chargepoint/{self.num}/set/log", asdict(self.data.set.log))

    def reset_log_data(self) -> None:
        self.data.set.log = Log()
        Pub().pub(f"openWB/set/chargepoint/{self.num}/set/log", asdict(self.data.set.log))

    def reset_control_parameter_at_charge_stop(self) -> None:
        # Wenn die Ladung zB wegen Autolock gestoppt wird, Zählerstände beibehalten, damit nicht nochmal die Ladung
        # gestartet wird.
        control_parameter = control_parameter_factory()
        self.data.control_parameter = control_parameter

    def initiate_control_pilot_interruption(self):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data.set.charging_ev_data
            # Unterstützt der Ladepunkt die CP-Unterbrechung und benötigt das Auto eine CP-Unterbrechung?
            if charging_ev.ev_template.data.control_pilot_interruption:
                if self.data.config.control_pilot_interruption_hw:
                    # Wird die Ladung gestartet?
                    if self.data.set.current_prev == 0 and self.data.set.current != 0:
                        # Die CP-Unterbrechung erfolgt in Threads, da diese länger als ein Zyklus dauert.
                        if thread_handler(Thread(
                                target=self.chargepoint_module.interrupt_cp,
                                args=(charging_ev.ev_template.data.control_pilot_interruption_duration,),
                                name=f"cp{self.chargepoint_module.config.id}")):
                            message = "Control-Pilot-Unterbrechung für " + str(
                                charging_ev.ev_template.data.control_pilot_interruption_duration) + "s."
                        self.set_state_and_log(message)
                else:
                    message = "CP-Unterbrechung nicht möglich, da der Ladepunkt keine CP-Unterbrechung unterstützt."
                    self.set_state_and_log(message)
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def check_deviating_contactor_states(self, phase_a: int, phase_b: int) -> bool:
        return (phase_a == 1 and phase_b in [2, 3]) or (phase_b == 1 and phase_a in [2, 3])

    def _is_phase_switch_required(self) -> bool:
        phase_switch_required = False
        # Manche EVs brauchen nach der Umschaltung mehrere Zyklen, bis sie mit den drei Phasen laden. Dann darf
        # nicht zwischendurch eine neue Umschaltung getriggert werden.
        if ((((self.data.control_parameter.state == ChargepointState.PHASE_SWITCH_AWAITED or
                self.data.control_parameter.state == ChargepointState.SWITCH_OFF_DELAY) and
                # Nach Ablauf der Laden aktiv halten Zeit, sollte mit der vorgegebenen Phasenzahl geladen werden.
            self.check_deviating_contactor_states(self.data.set.phases_to_use, self.data.get.phases_in_use)) or
                # Vorgegebene Phasenzahl hat sich geändert und es wird geladen
             (self.check_deviating_contactor_states(self.data.set.phases_to_use,
                                                    self.data.control_parameter.phases) and
                self.data.control_parameter.state in CHARGING_STATES)) and
                # Wenn ein Soll-Strom vorgegeben ist, muss das Auto auch laden, damit umgeschaltet wird, sonst
                # wird zB bei automatischer Umschaltung ständig versucht auf 1 Phase zurück zu schalten, wenn
                # das Auto bei 3 Phasen voll ist.
            ((self.data.set.current != 0 and self.data.get.charge_state) or
             (self.data.set.current != 0 and self.data.set.current_prev == 0) or
             self.data.set.current == 0)):
            phase_switch_required = True
        if (self.data.control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED and
            (self.check_deviating_contactor_states(self.data.set.phases_to_use, self.data.get.phases_in_use) or
                # Vorgegebene Phasenzahl hat sich geändert
             self.check_deviating_contactor_states(self.data.set.phases_to_use,
                                                   self.data.control_parameter.phases)) and
                # Wenn der Ladevorgang gestartet wird, muss vor dem ersten Laden umgeschaltet werden.
                self.data.set.current != 0):
            phase_switch_required = True
        if phase_switch_required:
            # Umschaltung fehlgeschlagen
            if self.data.set.phases_to_use != self.data.get.phases_in_use:
                if data.data.general_data.data.chargemode_config.retry_failed_phase_switches:
                    if self.data.control_parameter.failed_phase_switches > self.MAX_FAILED_PHASE_SWITCHES:
                        phase_switch_required = False
                        self.set_state_and_log(
                            "Keine Phasenumschaltung, da die maximale Anzahl an Fehlversuchen erreicht wurde. Die "
                            "aktuelle Phasenzahl wird bis zum Abstecken beibehalten.")
                else:
                    # Umschaltung vor Ladestart zulassen
                    if self.data.set.log.imported_since_plugged != 0:
                        phase_switch_required = False
                        self.set_state_and_log(
                            "Keine Phasenumschaltung, da wiederholtes Anstoßen der Umschaltung in den übergreifenden "
                            "Ladeeinstellungen deaktiviert wurde. Die aktuelle "
                            "Phasenzahl wird bis zum Abstecken beibehalten.")
                        self.data.control_parameter.failed_phase_switches += 1
        return phase_switch_required

    STOP_CHARGING = ", dafür wird die Ladung unterbrochen."

    def check_phase_switch_completed(self):
        try:
            evu_counter = data.data.counter_all_data.get_evu_counter()
            charging_ev = self.data.set.charging_ev_data
            # Umschaltung im Gange
            if self.data.control_parameter.state == ChargepointState.PERFORMING_PHASE_SWITCH:
                phase_switch_pause = charging_ev.ev_template.data.phase_switch_pause
                # Umschaltung abgeschlossen
                try:
                    timestamp_not_expired = timecheck.check_timestamp(
                        self.data.control_parameter.timestamp_last_phase_switch,
                        6 + phase_switch_pause - 1)
                except TypeError:
                    # so wird in jedem Fall die erforderliche Zeit abgewartet
                    self.data.control_parameter.timestamp_last_phase_switch = create_timestamp()
                    timestamp_not_expired = timecheck.check_timestamp(
                        self.data.control_parameter.timestamp_last_phase_switch,
                        6 + phase_switch_pause - 1)
                if not timestamp_not_expired:
                    log.debug("phase switch running")
                    # Aktuelle Ladeleistung und Differenz wieder freigeben.
                    if self.data.set.phases_to_use == 1:
                        evu_counter.data.set.reserved_surplus -= charging_ev.ev_template. \
                            data.max_current_single_phase * 230
                    else:
                        evu_counter.data.set.reserved_surplus -= charging_ev. \
                            ev_template.data.max_current_single_phase * 3 * 230
                    self.data.control_parameter.state = ChargepointState.WAIT_FOR_USING_PHASES
                else:
                    # Wenn eine Umschaltung im Gange ist, muss erst gewartet werden, bis diese fertig ist.
                    if self.data.set.phases_to_use == 1:
                        message = f"Umschaltung von {self.get_max_phase_hw()} auf 1 Phase{self.STOP_CHARGING}"
                    else:
                        message = f"Umschaltung von 1 auf {self.get_max_phase_hw()} Phasen{self.STOP_CHARGING}"
                    self.set_state_and_log(message)
                return
            if self.data.control_parameter.state == ChargepointState.WAIT_FOR_USING_PHASES:
                if check_timestamp(self.data.control_parameter.timestamp_charge_start,
                                   charging_ev.ev_template.data.keep_charge_active_duration) is False:
                    if self.cp_ev_support_phase_switch() and self.failed_phase_switches_reached():
                        if phase_switch.phase_switch_thread_alive(self.num) is False:
                            self.data.control_parameter.state = ChargepointState.PHASE_SWITCH_AWAITED
                            if self._is_phase_switch_required() is False:
                                self.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
                    else:
                        self.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def initiate_phase_switch(self):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            evu_counter = data.data.counter_all_data.get_evu_counter()
            charging_ev = self.data.set.charging_ev_data
            # Wenn noch kein Eintrag im Protokoll erstellt wurde, wurde noch nicht geladen und die Phase kann noch
            # umgeschaltet werden.
            if (not charging_ev.ev_template.data.prevent_phase_switch or
                    self.data.set.log.imported_since_plugged == 0):
                # Einmal muss die Anzahl der Phasen gesetzt werden.
                if self.data.set.phases_to_use == 0:
                    Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/phases_to_use",
                              self.data.control_parameter.phases)
                    self.data.set.phases_to_use = self.data.control_parameter.phases
                if self.cp_ev_support_phase_switch():
                    if self._is_phase_switch_required():
                        # Wenn die Umschaltverzögerung aktiv ist, darf nicht umgeschaltet werden.
                        if (self.data.control_parameter.state != ChargepointState.PERFORMING_PHASE_SWITCH and
                                (self.data.control_parameter.state != ChargepointState.WAIT_FOR_USING_PHASES or
                                 (self.data.control_parameter.state == ChargepointState.WAIT_FOR_USING_PHASES and
                                  self.data.get.charge_state is False))):
                            log.debug(
                                f"Lp {self.num}: Ladung aktiv halten "
                                f"{charging_ev.ev_template.data.keep_charge_active_duration}s")
                            if phase_switch.thread_phase_switch(self) is False:
                                return
                            log.debug("start phase switch phases_to_use " +
                                      str(self.data.set.phases_to_use) +
                                      " control_parameter phases " +
                                      str(self.data.control_parameter.phases))
                            if self.data.control_parameter.phases == 1:
                                message = f"Umschaltung von {self.get_max_phase_hw()} auf 1 Phase{self.STOP_CHARGING}"
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                evu_counter.data.set.reserved_surplus += charging_ev. \
                                    ev_template.data.max_current_single_phase * 230
                            else:
                                message = f"Umschaltung von 1 auf {self.get_max_phase_hw()} Phasen{self.STOP_CHARGING}"
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                evu_counter.data.set.reserved_surplus += charging_ev. \
                                    ev_template.data.max_current_single_phase * 3 * 230
                            # Timestamp für die Durchführungsdauer
                            self.data.control_parameter.timestamp_last_phase_switch = create_timestamp()
                            self.set_state_and_log(message)
                            if self.data.set.phases_to_use != self.data.control_parameter.phases:
                                Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/phases_to_use",
                                          self.data.control_parameter.phases)
                                self.data.set.phases_to_use = self.data.control_parameter.phases
                            self.data.control_parameter.state = ChargepointState.PERFORMING_PHASE_SWITCH
                        else:
                            log.error("Phasenumschaltung an Ladepunkt" + str(self.num) +
                                      " nicht möglich, da gerade eine Umschaltung im Gange ist.")
                    elif self.data.control_parameter.state == ChargepointState.PHASE_SWITCH_AWAITED:
                        # Wenn keine Phasenumschaltung durchgeführt wird, Status auf CHARGING_ALLOWED setzen, sonst
                        # bleibt PHASE_SWITCH_DELAY_EXPIRED stehen.
                        self.data.control_parameter.state = ChargepointState.CHARGING_ALLOWED
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.num))

    def get_phases_by_selected_chargemode(self, phases_chargemode: int) -> int:
        charging_ev = self.data.set.charging_ev_data
        if ((self.data.config.auto_phase_switch_hw is False and self.data.get.charge_state) or
                self.data.control_parameter.failed_phase_switches > self.MAX_FAILED_PHASE_SWITCHES):
            # Wenn keine Umschaltung verbaut ist, die Phasenzahl nehmen, mit der geladen wird. Damit werden zB auch
            # einphasige EV an dreiphasigen openWBs korrekt berücksichtigt.
            phases = self.data.get.phases_in_use or self.data.set.phases_to_use
        elif self.data.control_parameter.state == ChargepointState.PERFORMING_PHASE_SWITCH:
            phases = self.data.set.phases_to_use
            log.debug(f"Umschaltung wird durchgeführt, Phasenzahl nicht ändern {phases}")
        elif phases_chargemode == 0:
            # Wenn die Lademodus-Phasen 0 sind, wird die bisher genutzte Phasenzahl weiter genutzt,
            # bis der Algorithmus eine Umschaltung vorgibt, zB weil der gewählte Lademodus eine
            # andere Phasenzahl benötigt oder bei PV-Laden die automatische Umschaltung aktiv ist.
            if self.data.get.charge_state:
                phases = self.data.set.phases_to_use
            else:
                if ((not charging_ev.ev_template.data.prevent_phase_switch or
                        self.data.set.log.imported_since_plugged == 0) and
                        self.data.config.auto_phase_switch_hw):
                    phases = 1
                else:
                    if self.data.set.phases_to_use != 0:
                        phases = self.data.set.phases_to_use
                    else:
                        # phases_target
                        phases = self.data.config.connected_phases
            log.debug(f"Phasenzahl Lademodus: {phases}")
        else:
            if phases_chargemode == 0:
                phases = self.data.control_parameter.phases
            else:
                phases = phases_chargemode
        return phases

    def get_max_phase_hw(self) -> int:
        charging_ev = self.data.set.charging_ev_data
        config = self.data.config

        phases = min(charging_ev.ev_template.data.max_phases, config.connected_phases)
        if charging_ev.ev_template.data.max_phases <= config.connected_phases:
            log.debug(f"EV-Phasenzahl beschränkt die nutzbaren Phasen auf {phases}")
        else:
            log.debug(f"Anzahl angeschlossener Phasen beschränkt die nutzbaren Phasen auf {phases}")
        return phases

    def set_phases(self, phases: int) -> int:
        charging_ev = self.data.set.charging_ev_data

        if phases != self.data.get.phases_in_use:
            # Wenn noch kein Eintrag im Protokoll erstellt wurde, wurde noch nicht geladen und die Phase kann noch
            # umgeschaltet werden.
            if self.data.set.log.imported_since_plugged != 0:
                if charging_ev.ev_template.data.prevent_phase_switch:
                    log.info(f"Phasenumschaltung an Ladepunkt {self.num} nicht möglich, da bei EV"
                             f"{charging_ev.num} nach Ladestart nicht mehr umgeschaltet werden darf.")
                    if self.data.get.phases_in_use != 0:
                        phases = self.data.get.phases_in_use
                    else:
                        phases = self.data.control_parameter.phases
                elif self.cp_ev_support_phase_switch() is False:
                    # sonst passt die Phasenzahl nicht bei Autos, die eine Phase weg schalten.
                    log.info(f"Phasenumschaltung an Ladepunkt {self.num} wird durch die Hardware nicht unterstützt.")
                    phases = phases
        if phases != self.data.control_parameter.phases:
            self.data.control_parameter.phases = phases
        return phases

    def check_min_max_current(self, required_current: float, phases: int, pv: bool = False) -> float:
        required_current_prev = required_current
        required_current, msg = self.data.set.charging_ev_data.check_min_max_current(
            self.data.control_parameter,
            required_current,
            phases,
            self.template.data.charging_type,
            pv)
        if self.template.data.charging_type == ChargingType.AC.value:
            if phases == 1:
                required_current = min(required_current, self.template.data.max_current_single_phase)
            else:
                required_current = min(required_current, self.template.data.max_current_multi_phases)
        else:
            required_current = min(required_current, self.template.data.dc_max_current)
        if required_current != required_current_prev and msg is None:
            msg = ("Die Einstellungen in dem Ladepunkt-Profil beschränken den Strom auf "
                   f"maximal {required_current} A.")
        self.set_state_and_log(msg)
        return required_current

    def set_required_currents(self, required_current: float) -> None:
        control_parameter = self.data.control_parameter
        try:
            for i in range(0, control_parameter.phases):
                evu_phase = convert_single_evu_phase_to_cp_phase(self.data.config.phase_1, i)
                control_parameter.required_currents[evu_phase] = required_current
        except KeyError:
            control_parameter.required_currents = [required_current]*3
            self.set_state_and_log("Bitte in den Ladepunkt-Einstellungen die Einstellung 'Phase 1 des Ladekabels'" +
                                   " angeben. Andernfalls wird der benötigte Strom auf allen 3 Phasen vorgehalten, " +
                                   "was ggf eine unnötige Reduktion der Ladeleistung zur Folge hat.")
        self.data.set.required_power = sum(
            [c * v for c, v in zip(control_parameter.required_currents, self.data.get.voltages)])

    def set_timestamp_charge_start(self):
        # Beim Ladestart Timer laufen lassen, manche Fahrzeuge brauchen sehr lange.
        # Nach dem Algorithmus setzen, sonst steht set current noch nicht fest.
        if self.data.control_parameter.timestamp_charge_start is None:
            if self.data.set.current_prev == 0 and self.data.set.current != 0:
                self.data.control_parameter.timestamp_charge_start = create_timestamp()
        elif self.data.set.current == 0:
            self.data.control_parameter.timestamp_charge_start = None

    def set_chargemode_changed(self, submode: str) -> None:
        if ((submode == "time_charging" and self.data.control_parameter.chargemode != "time_charging") or
                (submode != "time_charging" and
                 self.data.control_parameter.chargemode != self.data.set.charge_template.data.chargemode.selected)):
            self.chargemode_changed = True
            log.debug("Änderung des Lademodus")
            self.data.control_parameter.timestamp_chargemode_changed = create_timestamp()
        else:
            self.chargemode_changed = False

    def set_submode_changed(self, submode: str) -> None:
        self.submode_changed = (submode != self.data.control_parameter.submode)

    def update_ev(self, ev_list: Dict[str, Ev]) -> None:
        self._validate_rfid()
        charging_possible = self.is_charging_possible()[0]
        if charging_possible:
            vehicle = self.template.get_ev(self.data.get.rfid or self.data.set.rfid,
                                           self.data.get.vehicle_id,
                                           self.data.config.ev)[0]
            charging_ev = self._get_charging_ev(vehicle, ev_list)
            self._pub_connected_vehicle(charging_ev)
        else:
            vehicle = -1
            self._pub_configured_ev(ev_list)
            if self.data.config.ev != self.data.set.ev_prev:
                self.update_charge_template(ev_list[f"ev{self.data.config.ev}"].charge_template)

    def update(self, ev_list: Dict[str, Ev]) -> None:
        try:
            self._validate_rfid()
            charging_possible, message = self.is_charging_possible()
            if self.data.get.rfid is not None and self.data.get.plug_state:
                self._link_rfid_to_cp()
            vehicle, message_ev = self.template.get_ev(self.data.set.rfid or self.data.get.rfid,
                                                       self.data.get.vehicle_id,
                                                       self.data.config.ev)
            if message_ev:
                message += message_ev

            if charging_possible:
                try:
                    charging_ev = self._get_charging_ev(vehicle, ev_list)
                    max_phase_hw = self.get_max_phase_hw()
                    state, message_ev, submode, required_current, phases = charging_ev.get_required_current(
                        self.data.set.charge_template,
                        self.data.control_parameter,
                        max_phase_hw,
                        self.cp_ev_support_phase_switch(),
                        self.template.data.charging_type,
                        self.data.control_parameter.timestamp_chargemode_changed or create_timestamp(),
                        self.data.set.log.imported_since_plugged)
                    phases = self.get_phases_by_selected_chargemode(phases)
                    phases = self.set_phases(phases)
                    self._pub_connected_vehicle(charging_ev)
                    required_current = self.chargepoint_module.add_conversion_loss_to_current(required_current)
                    # Einhaltung des Minimal- und Maximalstroms prüfen
                    required_current = self.check_min_max_current(
                        required_current, self.data.control_parameter.phases)
                    required_current = self.chargepoint_module.add_conversion_loss_to_current(required_current)
                    self.set_chargemode_changed(submode)
                    self.set_submode_changed(submode)
                    self.set_control_parameter(submode, required_current)
                    self.set_required_currents(required_current)
                    self.check_phase_switch_completed()

                    if self.chargemode_changed or self.submode_changed:
                        data.data.counter_all_data.get_evu_counter().reset_switch_on_off(
                            self, charging_ev)
                        charging_ev.reset_phase_switch(self.data.control_parameter)
                    message = message_ev if message_ev else message
                    # Ein Eintrag muss nur erstellt werden, wenn vorher schon geladen wurde und auch danach noch
                    # geladen werden soll.
                    if self.chargemode_changed and self.data.set.log.imported_since_mode_switch != 0 and state:
                        chargelog.save_interim_data(self, charging_ev)

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
                        log.debug(f'LP {self.num}, EV: {self.data.set.charging_ev_data.data.name}'
                                  f' (EV-Nr.{vehicle}): Lademodus '
                                  f'{self.data.set.charge_template.data.chargemode.selected}, Submodus: '
                                  f'{self.data.control_parameter.submode}')
                    else:
                        if (self.data.control_parameter.state == ChargepointState.SWITCH_ON_DELAY and
                                data.data.counter_all_data.get_evu_counter().data.set.reserved_surplus == 0):
                            log.error("Reservierte Leistung kann nicht 0 sein.")

                        log.info(
                            f"LP {self.num}, EV: {self.data.set.charging_ev_data.data.name} (EV-Nr.{vehicle}): "
                            f"Theoretisch benötigter Strom {required_current}A, Lademodus "
                            f"{self.data.set.charge_template.data.chargemode.selected}, Submodus: "
                            f"{self.data.control_parameter.submode}, Phasen: "
                            f"{self.data.control_parameter.phases}"
                            f", Priorität: {self.data.control_parameter.prio}"
                            f", mittlerer Ist-Strom: {get_medium_charging_current(self.data.get.currents)}")
                except Exception:
                    log.exception("Fehler im Prepare-Modul für Ladepunkt "+str(self.num))
                    self.data.control_parameter.submode = "stop"
            else:
                self._process_charge_stop()
                if vehicle != -1:
                    self._pub_connected_vehicle(ev_list[f"ev{vehicle}"])
                    if self.data.set.charge_template.data.id != ev_list[f"ev{vehicle}"].charge_template.data.id:
                        self.update_charge_template(ev_list[f"ev{vehicle}"].charge_template)
                else:
                    self._pub_configured_ev(ev_list)
                    if self.data.set.charge_template.data.id != ev_list[
                            f"ev{self.data.config.ev}"].charge_template.data.id:
                        self.update_charge_template(ev_list[f"ev{self.data.config.ev}"].charge_template)
            try:
                # check für charging stop or charging interruption, if so force a soc query for the ev
                if self.data.set.charge_state_prev and self.data.get.charge_state is False:
                    Pub().pub(f"openWB/set/vehicle/{self.data.config.ev}/get/force_soc_update", True)
                    log.info(f"SoC-Abfrage nach Ladeunterbrechung, cp{self.num}, ev{self.data.config.ev}")
            except Exception:
                log.exception(f"Fehler bei Ladestop,cp{self.num}")

            # OCPP Start Transaction nach Anstecken
            if ((self.data.get.plug_state and self.data.set.plug_state_prev is False) or
                    (self.data.set.ocpp_transaction_id is None and self.data.get.charge_state)):
                self.data.set.ocpp_transaction_id = data.data.optional_data.start_transaction(
                    self.data.config.ocpp_chargebox_id,
                    self.chargepoint_module.fault_state,
                    self.num,
                    self.data.set.rfid or self.data.get.rfid or self.data.get.vehicle_id,
                    self.data.get.imported)
                Pub().pub("openWB/set/chargepoint/"+str(self.num) +
                          "/set/ocpp_transaction_id", self.data.set.ocpp_transaction_id)
            if self.data.get.plug_state and self.data.set.plug_state_prev is False:
                self.data.control_parameter.timestamp_chargemode_changed = create_timestamp()
            # SoC nach Anstecken aktualisieren
            if ((self.data.get.plug_state and self.data.set.plug_state_prev is False) or
                    (self.data.get.plug_state is False and self.data.set.plug_state_prev) or
                    (self.data.get.soc_timestamp and self.data.set.charging_ev_data.data.get.soc_timestamp and
                        self.data.get.soc_timestamp > self.data.set.charging_ev_data.data.get.soc_timestamp)):
                Pub().pub(f"openWB/set/vehicle/{self.data.config.ev}/get/force_soc_update", True)
                log.debug("SoC nach Anstecken")
            self.set_state_and_log(message)
        except Exception:
            log.exception(f"Fehler bei Ladepunkt {self.num}")

    def _pub_configured_ev(self, ev_list: Dict[str, Ev]) -> None:
        # Wenn kein EV zur Ladung zugeordnet wird, auf hinterlegtes EV zurückgreifen.
        try:
            self._pub_connected_vehicle(ev_list[f"ev{self.data.config.ev}"])
        except KeyError:
            log.error(f"EV {self.data.config.ev} konnte nicht gefunden werden, daher wird das " +
                      "Standardfahrzeug verwendet.")
            self._pub_connected_vehicle(ev_list["ev0"])

    def _get_charging_ev(self, vehicle: int, ev_list: Dict[str, Ev]) -> Ev:
        try:
            charging_ev = ev_list[f"ev{vehicle}"]
        except KeyError:
            log.error(f"EV {vehicle} konnte nicht gefunden werden, daher wird das Standardfahrzeug" +
                      " verwendet.")
            charging_ev = ev_list["ev0"]
            vehicle = 0
        if (self.data.set.charging_ev != -1 and self.data.set.charging_ev != vehicle and
                self.data.set.charging_ev_prev != 1 and self.data.set.charging_ev_prev != vehicle):
            Pub().pub(f"openWB/set/vehicle/{charging_ev.num}/get/force_soc_update", True)
            log.debug("SoC nach EV-Wechsel")
            self.update_charge_template(charging_ev.charge_template)
        if self.data.set.charge_template.data.id != charging_ev.charge_template.data.id:
            self.update_charge_template(charging_ev.charge_template)
        self.data.set.charging_ev_data = charging_ev
        self.data.set.charging_ev = vehicle
        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev", vehicle)
        self.data.set.charging_ev_prev = vehicle
        Pub().pub("openWB/set/chargepoint/"+str(self.num)+"/set/charging_ev_prev", vehicle)
        return charging_ev

    def _clear_template_topics(self, topic: str) -> None:
        def on_connect(client, userdata, flags, rc):
            client.subscribe(topic, 2)

        def __get_payload(client, userdata, msg):
            received_topics.append(msg.topic)
        received_topics = []
        BrokerClient("processBrokerBranch", on_connect, __get_payload).start_finite_loop()
        for topic in received_topics:
            Pub().pub(topic, "")

    def update_charge_template(self, charge_template: ChargeTemplate) -> None:
        Pub().pub(f'openWB/chargepoint/{self.num}/set/charge_template', "")
        Pub().pub(f"openWB/set/chargepoint/{self.num}/set/charge_template",
                  dataclasses.asdict(charge_template.data))

    def _pub_connected_vehicle(self, vehicle: Ev):
        """ published die Daten, die zur Anzeige auf der Hauptseite benötigt werden.

        Parameter
        ---------
        vehicle: dict
            EV, das dem LP zugeordnet ist
        cp_num: int
            LP-Nummer
        """
        try:
            soc_obj = ConnectedSoc(
                range_charged=self.data.set.log.range_charged,
                range_unit=data.data.general_data.data.range_unit,
            )
            if vehicle.soc_module is not None:
                soc_obj.timestamp = vehicle.data.get.soc_timestamp
                soc_obj.soc = vehicle.data.get.soc
                soc_obj.fault_state = vehicle.data.get.fault_state
                soc_obj.fault_str = vehicle.data.get.fault_str
                soc_obj.range = vehicle.data.get.range
            info_obj = ConnectedInfo(id=vehicle.num,
                                     name=vehicle.data.name)
            if (self.data.set.charge_template.data.chargemode.selected == "time_charging" or
                    self.data.set.charge_template.data.chargemode.selected == "scheduled_charging"):
                current_plan = self.data.control_parameter.current_plan
            else:
                current_plan = None
            config_obj = ConnectedConfig(
                charge_template=self.data.set.charge_template.data.id,
                ev_template=vehicle.ev_template.data.id,
                chargemode=self.data.set.charge_template.data.chargemode.selected,
                priority=self.data.set.charge_template.data.prio,
                current_plan=current_plan,
                average_consumption=vehicle.ev_template.data.average_consump,
                time_charging_in_use=True if (self.data.control_parameter.submode ==
                                              "time_charging") else False)
            if soc_obj != self.data.get.connected_vehicle.soc:
                Pub().pub(f"openWB/chargepoint/{self.num}/get/connected_vehicle/soc", dataclasses.asdict(soc_obj))
            if info_obj != self.data.get.connected_vehicle.info:
                Pub().pub(f"openWB/chargepoint/{self.num}/get/connected_vehicle/info", dataclasses.asdict(info_obj))
            if config_obj != self.data.get.connected_vehicle.config:
                Pub().pub(f"openWB/chargepoint/{self.num}/get/connected_vehicle/config",
                          dataclasses.asdict(config_obj))
        except Exception:
            log.exception("Fehler im Prepare-Modul")

    def cp_ev_chargemode_support_phase_switch(self) -> bool:
        if (self.cp_ev_support_phase_switch() and
                self.data.get.charge_state and
                self.chargemode_support_phase_switch() and
                (self.data.control_parameter.state == ChargepointState.CHARGING_ALLOWED or
                 self.data.control_parameter.state == ChargepointState.PHASE_SWITCH_DELAY)):
            return self.failed_phase_switches_reached()
        else:
            return False

    def cp_ev_support_phase_switch(self) -> bool:
        return (self.data.config.auto_phase_switch_hw and
                self.data.set.charging_ev_data.ev_template.data.prevent_phase_switch is False)

    def chargemode_support_phase_switch(self) -> bool:
        control_parameter = self.data.control_parameter
        pv_auto_switch = ((control_parameter.chargemode == Chargemode.PV_CHARGING or
                           control_parameter.chargemode == Chargemode.ECO_CHARGING) and
                          control_parameter.submode == Chargemode.PV_CHARGING and
                          self.data.set.charge_template.data.chargemode.pv_charging.phases_to_use == 0)
        scheduled_auto_switch = (
            control_parameter.chargemode == Chargemode.SCHEDULED_CHARGING and
            control_parameter.submode == Chargemode.PV_CHARGING and
            self.data.set.charge_template.data.chargemode.scheduled_charging.plans[
                str(self.data.control_parameter.current_plan)].phases_to_use_pv == 0)
        return (pv_auto_switch or scheduled_auto_switch)

    def failed_phase_switches_reached(self) -> bool:
        if ((data.data.general_data.data.chargemode_config.retry_failed_phase_switches and
             self.data.control_parameter.failed_phase_switches > self.MAX_FAILED_PHASE_SWITCHES) or
            (data.data.general_data.data.chargemode_config.retry_failed_phase_switches is False and
             self.data.control_parameter.failed_phase_switches == 1)):
            self.set_state_and_log(
                "Keine automatische Umschaltung, da die maximale Anzahl an Fehlversuchen erreicht wurde. ")
            return False
        else:
            return True
