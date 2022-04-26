"""Ladepunkt-Logik

charging_ev: EV, das aktuell laden darf
charging_ev_prev: EV, das vorher geladen hat. Dies wird benötigt, da wenn das EV nicht mehr laden darf, z.B. weil
Autolock aktiv ist, gewartet werden muss, bis die Ladeleistung 0 ist und dann erst der Logeintrag erstellt werden kann.
charging_ev = -1 zeigt an, dass der LP im Algorithmus nicht berücksichtigt werden soll. Ist das Ev abgesteckt, wird
auch charging_ev_prev -1 und im nächsten Zyklus kann ein neues Profil geladen werden.

RFID-Tags/Code-Eingabe:
Mit einem Tag/Code kann optional der Ladepunkt freigeschaltet werden, es wird geleichzeitig immer ein EV damit
zugeordnet, mit dem nach der Freischaltung geladen werden soll. Wenn max 5 Min nach dem Scannen kein Auto
angesteckt wird, wird der Tag verworfen. Ebenso wenn kein EV gefunden wird.
Tag-Liste: Tags, mit denen der Ladepunkt freigeschaltet werden kann. Ist diese leer, kann mit jedem Tag der Ladepunkt
freigeschaltet werden.
"""
import logging
import traceback
from typing import Optional, Tuple

from control import chargelog
from control import cp_interruption
from control import data
from control import ev
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


class AllChargepoints:
    """
    """

    def __init__(self):
        self.data = {"get": {"daily_imported": 0,
                             "daily_exported": 0}}
        Pub().pub("openWB/set/chargepoint/get/power", 0)

    def no_charge(self):
        """ Wenn keine EV angesteckt sind oder keine EV laden/laden möchten, werden die Algorithmus-Werte
        zurückgesetzt.
        (dient der Robustheit)
        """
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        # Kein EV angesteckt
                        if (not chargepoint.data["get"]["plug_state"] or
                                # Kein EV, das Laden soll
                                chargepoint.data["set"]["charging_ev"] == -1 or
                                # Kein EV, das auf das Ablaufen der Einschalt- oder Phasenumschaltverzögerung wartet
                                (chargepoint.data["set"]["charging_ev"] != -1 and
                                 chargepoint.data["set"]["charging_ev_data"].data["control_parameter"][
                                     "timestamp_perform_phase_switch"] is None and
                                 chargepoint.data["set"]["charging_ev_data"].data["control_parameter"][
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
                        power = power + chargepoint.data["get"]["power"]
                        imported = imported + chargepoint.data["get"]["imported"]
                        exported = exported + chargepoint.data["get"]["exported"]
                except Exception:
                    log.exception("Fehler in der allgemeinen Ladepunkt-Klasse für Ladepunkt "+cp)
            self.data["get"]["power"] = power
            Pub().pub("openWB/set/chargepoint/get/power", power)
            self.data["get"]["imported"] = imported
            Pub().pub("openWB/set/chargepoint/get/imported", imported)
            self.data["get"]["exported"] = exported
            Pub().pub("openWB/set/chargepoint/get/exported", exported)
        except Exception:
            log.exception("Fehler in der allgemeinen Ladepunkt-Klasse")


class Chargepoint:
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf.
    """

    def __init__(self, index):
        try:
            self.template: CpTemplate = None
            self.chargepoint_module: AbstractChargepoint = None
            self.cp_num = index
            # set current aus dem vorherigen Zyklus, um zu wissen, ob am Ende des Zyklus die Ladung freigegeben wird
            # (für Control-Pilot-Unterbrechung)
            self.set_current_prev = 0
            # bestehende Daten auf dem Broker nicht zurücksetzen, daher nicht publishen
            self.data = {
                "set": {"charging_ev": -1,
                        "charging_ev_prev": -1,
                        "autolock_state": 0,
                        "current": 0,
                        "energy_to_charge": 0,
                        "plug_time": None,
                        "rfid": None,
                        "manual_lock": False,
                        "loadmanagement_available": True,
                        "log": {"imported_at_plugtime": 0,
                                "timestamp_start_charging": None,
                                "imported_at_mode_switch": 0,
                                "imported_since_mode_switch": 0,
                                "imported_since_plugged": 0,
                                "range_charged": 0,
                                "time_charged": "00:00",
                                "chargemode_log_entry": "_"}},
                "get": {
                    "rfid_timestamp": None,
                    "rfid": None,
                    "daily_imported": 0,
                    "daily_exported": 0,
                    "plug_state": False,
                    "charge_state": False,
                    "power": 0,
                    "imported": 0,
                    "exported": 0,
                    "connected_vehicle": {"soc_config": {},
                                          "soc": {},
                                          "info": {},
                                          "config": {}}}}
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

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
        if self.data["set"]["loadmanagement_available"]:
            state = True
            message = None
        else:
            state = False
            message = "Ladepunkt gesperrt, da keine Werte vom EVU-Zähler empfangen wurden und deshalb kein \
            Lastmanagement durchgeführt werden kann. Falls Sie dennoch laden möchten, können Sie als EVU-Zähler \
                'Virtuell' auswählen und einen konstanten Hausverbrauch angeben."
        return state, message

    def _is_autolock_inactive(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob Autolock nicht aktiv ist oder ob die Sperrung durch einen dem LP zugeordneten RFID-Tag aufgehoben
        werden kann.
        """
        message = None
        state = self.template.autolock(
            self.data["set"]["autolock_state"],
            self.data["get"]["charge_state"],
            self.cp_num)
        if not state:
            state = True
        else:
            # Darf Autolock durch Tag überschrieben werden?
            if (data.data.optional_data["optional"].data["rfid"]["active"] and
                    self.template.data["rfid_enabling"]):
                if self.data["get"]["rfid"] is None and self.data["set"]["rfid"] is None:
                    state = False
                    message = "Keine Ladung, da der Ladepunkt durch Autolock gesperrt ist und erst per RFID \
                        freigeschaltet werden muss."
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
        if (self.data["set"]["manual_lock"] is False or
                (self.template.data["rfid_enabling"] and
                    (self.data["get"]["rfid"] is not None or self.data["set"]["rfid"] is not None))):
            charging_possbile = True
            message = None
        else:
            charging_possbile = False
            message = "Keine Ladung, da der Ladepunkt manuell gesperrt wurde."
        return charging_possbile, message

    def _is_ev_plugged(self) -> Tuple[bool, Optional[str]]:
        """ prüft, ob ein EV angesteckt ist
        """
        state = self.data["get"]["plug_state"]
        if not state:
            message = "Keine Ladung, da kein Auto angesteckt ist."
        else:
            if self.data["set"]["plug_time"] is None:
                self.data["set"]["plug_time"] = timecheck.create_timestamp()
                Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/plug_time",
                          self.data["set"]["plug_time"])
            message = None
        return state, message

    def get_state(self):
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
            if "current" not in self.data["set"]:
                self.set_current_prev = 0
            else:
                self.set_current_prev = self.data["set"]["current"]
            self.__validate_rfid()
            message = "Keine Ladung, da ein Fehler aufgetreten ist."
            charging_possbile = False
            try:
                state, message = self._is_grid_protection_inactive()
                if state:
                    state, message = self._is_ripple_control_receiver_inactive()
                    if state:
                        state, message = self._is_loadmanagement_available()
                        if state:
                            state, message = self._is_ev_plugged()
                            if state:
                                state, message = self._is_autolock_inactive()
                                if state:
                                    charging_possbile, message = self._is_manual_lock_inactive()
            except Exception:
                log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
                return False, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()
            if charging_possbile:
                ev_num, message = self.template.get_ev(self.data["get"]["rfid"], self.data["config"]["ev"])
                if ev_num != -1:
                    if self.data["get"]["rfid"] is not None:
                        self.__link_rfid_to_cp()
                    return ev_num, message
                else:
                    self.data["get"]["state_str"] = message
            # Charging Ev ist noch das EV des vorherigen Zyklus, wenn das nicht -1 war und jetzt nicht mehr geladen
            # werden soll (-1), Daten zurücksetzen.
            if self.data["set"]["charging_ev"] != -1:
                # Altes EV merken
                self.data["set"]["charging_ev_prev"] = self.data["set"]["charging_ev"]
                Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/charging_ev_prev",
                          self.data["set"]["charging_ev_prev"])
            if self.data["set"]["charging_ev_prev"] != -1:
                # Daten zurücksetzen, wenn nicht geladen werden soll.
                data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])].reset_ev()
                data.data.pv_data["all"].reset_switch_on_off(
                    self, data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])])
                # Abstecken
                if not self.data["get"]["plug_state"]:
                    # Standardprofil nach Abstecken laden
                    if data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])].charge_template.data[
                            "load_default"]:
                        self.data["config"]["ev"] = 0
                        Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/config/ev", 0)
                    # Ladepunkt nach Abstecken sperren
                    if data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])].charge_template.data[
                            "disable_after_unplug"]:
                        self.data["set"]["manual_lock"] = True
                        Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/manual_lock", True)
                    # Ev wurde noch nicht aktualisiert.
                    chargelog.reset_data(self, data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])])
                    self.data["set"]["charging_ev_prev"] = -1
                    Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/charging_ev_prev",
                              self.data["set"]["charging_ev_prev"])
                    self.data["set"]["rfid"] = None
                    Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/rfid", None)
                    self.data["set"]["plug_time"] = None
                    Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/plug_time", None)
                    self.data["set"]["phases_to_use"] = self.data["get"]["phases_in_use"]
                    Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use",
                              self.data["set"]["phases_to_use"])
            self.data["set"]["charging_ev"] = -1
            Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/charging_ev", -1)
            self.data["set"]["current"] = 0
            Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/current", 0)
            self.data["set"]["energy_to_charge"] = 0
            Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/energy_to_charge", 0)
            return -1, message
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return -1, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def initiate_control_pilot_interruption(self):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data["set"]["charging_ev_data"]
            # Unterstützt der Ladepunkt die CP-Unterbrechung und benötigt das Auto eine CP-Unterbrechung?
            if charging_ev.ev_template.data["control_pilot_interruption"]:
                if self.data["config"]["control_pilot_interruption_hw"]:
                    # Wird die Ladung gestartet?
                    if self.set_current_prev == 0 and self.data["set"]["current"] != 0:
                        cp_interruption.thread_cp_interruption(self.cp_num,
                                                               self.chargepoint_module,
                                                               charging_ev.ev_template.data[
                                                                   "control_pilot_interruption_duration"])
                        message = "Control-Pilot-Unterbrechung für " + str(
                            charging_ev.ev_template.data["control_pilot_interruption_duration"]) + "s."
                        log.info("LP "+str(self.cp_num)+": "+message)
                        self.data["get"]["state_str"] = message
                else:
                    message = "CP-Unterbrechung nicht möglich, da der Ladepunkt keine CP-Unterbrechung unterstützt."
                    log.info("LP "+str(self.cp_num)+": "+message)
                    self.data["get"]["state_str"] = message
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

    def initiate_phase_switch(self):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data["set"]["charging_ev_data"]
            # Umschaltung im Gange
            if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] is not None:
                phase_switch_pause = charging_ev.ev_template.data["phase_switch_pause"]
                # Umschaltung abgeschlossen
                if not timecheck.check_timestamp(
                        charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"],
                        6 + phase_switch_pause - 1):
                    log.debug("phase switch running")
                    charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] = None
                    Pub().pub("openWB/set/vehicle/" + str(charging_ev.ev_num) +
                              "/control_parameter/timestamp_perform_phase_switch", None)
                    # Aktuelle Ladeleistung und Differenz wieder freigeben.
                    if charging_ev.data["control_parameter"]["phases"] == 3:
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= charging_ev.data[
                            "control_parameter"]["required_current"] * 3 * 230
                    elif charging_ev.data["control_parameter"]["phases"] == 1:
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= charging_ev.ev_template.data[
                            "max_current_one_phase"] * 230
                    self.data["set"]["current"] = charging_ev.data["control_parameter"]["required_current"]
                else:
                    # Wenn eine Umschaltung im Gange ist, muss erst gewartet werden, bis diese fertig ist.
                    if self.data["set"]["phases_to_use"] == 3:
                        message = "Umschaltung von 1 auf 3 Phasen."
                    elif self.data["set"]["phases_to_use"] == 1:
                        message = "Umschaltung von 3 auf 1 Phase."
                    else:
                        raise ValueError(str(self.data["set"]["phases_to_use"])+" ist keine gültige Phasenzahl (1/3).")
                    self.data["get"]["state_str"] = message
                return
            # Wenn noch kein Logeintrag erstellt wurde, wurde noch nicht geladen und die Phase kann noch umgeschaltet
            # werden.
            if not charging_ev.ev_template.data["prevent_phase_switch"] or self.data["set"]["log"][
                    "imported_since_plugged"] == 0:
                # Einmal muss die Anzahl der Phasen gesetzt werden.
                if "phases_to_use" not in self.data["set"]:
                    Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use",
                              charging_ev.data["control_parameter"]["phases"])
                    self.data["set"]["phases_to_use"] = charging_ev.data["control_parameter"]["phases"]
                # Manche EVs brauchen nach der Umschaltung mehrere Zyklen, bis sie mit den drei Phasen laden. Dann darf
                # nicht zwischendurch eine neue Umschaltung getriggert werden.
                if self.data["set"]["phases_to_use"] != charging_ev.data["control_parameter"]["phases"]:
                    # Wenn die Umschaltverzögerung aktiv ist, darf nicht umgeschaltet werden.
                    if charging_ev.data["control_parameter"]["timestamp_auto_phase_switch"] is None:
                        if self.data["config"]["auto_phase_switch_hw"]:
                            charge_state = self.data["get"]["charge_state"]
                            phase_switch.thread_phase_switch(
                                self.cp_num, self.chargepoint_module, charging_ev.data["control_parameter"]["phases"],
                                charging_ev.ev_template.data["phase_switch_pause"],
                                charge_state)
                            log.debug("start phase switch phases_to_use " +
                                      str(self.data["set"]["phases_to_use"]) +
                                      "control_parameter phases " +
                                      str(charging_ev.data["control_parameter"]["phases"]))
                            # 1 -> 3
                            if charging_ev.data["control_parameter"]["phases"] == 3:
                                message = "Umschaltung von 1 auf 3 Phasen."
                                log.info("LP "+str(self.cp_num)+": "+message)
                                self.data["get"]["state_str"] = message
                                # Timestamp für die Durchführungsdauer
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] += charging_ev.data[
                                    "control_parameter"]["required_current"] * 3 * 230
                                charging_ev.data["control_parameter"][
                                    "timestamp_perform_phase_switch"] = timecheck.create_timestamp()
                                Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                                          "/control_parameter/timestamp_perform_phase_switch",
                                          charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"])
                            elif charging_ev.data["control_parameter"]["phases"] == 1:
                                message = "Umschaltung von 3 auf 1 Phase."
                                # Timestamp für die Durchführungsdauer
                                charging_ev.data["control_parameter"][
                                    "timestamp_perform_phase_switch"] = timecheck.create_timestamp()
                                Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                                          "/control_parameter/timestamp_perform_phase_switch",
                                          charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"])
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                data.data.pv_data["all"].data["set"][
                                    "reserved_evu_overhang"] += charging_ev.ev_template.data[
                                        "max_current_one_phase"] * 230
                                log.info("LP "+str(self.cp_num)+": "+message)
                                self.data["get"]["state_str"] = message
                        else:
                            log.error(
                                "Phasenumschaltung an Ladepunkt" + str(self.cp_num) +
                                " nicht möglich, da der Ladepunkt keine Phasenumschaltung unterstützt.")
                    else:
                        log.error("Phasenumschaltung an Ladepunkt" + str(self.cp_num) +
                                  " nicht möglich, da gerade eine Umschaltung im Gange ist.")
            if self.data["set"]["phases_to_use"] != charging_ev.data["control_parameter"]["phases"]:
                Pub().pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use",
                          charging_ev.data["control_parameter"]["phases"])
                self.data["set"]["phases_to_use"] = charging_ev.data["control_parameter"]["phases"]
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

    def get_phases(self, mode):
        """ ermittelt die maximal mögliche Anzahl Phasen, die von Konfiguration, Auto und Ladepunkt unterstützt wird
        und prüft anschließend, ob sich die Anzahl der genutzten Phasen geändert hat.
        Return
        ------
        phases: int
            Anzahl Phasen
        """
        try:
            phases = 0
            charging_ev = self.data["set"]["charging_ev_data"]
            config = self.data["config"]
            if charging_ev.ev_template.data["max_phases"] <= config["connected_phases"]:
                phases = charging_ev.ev_template.data["max_phases"]
                log.debug("EV-Phasenzahl beschränkt die nutzbaren Phasen auf "+str(phases))
            else:
                phases = config["connected_phases"]
                log.debug("Anzahl angeschlossener Phasen beschränkt die nutzbaren Phasen auf "+str(phases))
            chargemode_phases = data.data.general_data["general"].get_phases_chargemode(mode)
            # Wenn die Lademodus-Phasen 0 sind, wird die bisher genutzte Phasenzahl weiter genutzt,
            # bis der Algorithmus eine Umschaltung vorgibt, zB weil der gewählte Lademodus eine
            # andere Phasenzahl benötigt oder bei PV-Laden die automatische Umschaltung aktiv ist.
            if chargemode_phases == 0:
                if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] is None:
                    if self.data["get"]["charge_state"]:
                        phases = self.data["set"]["phases_to_use"]
                    else:
                        if ((not charging_ev.ev_template.data["prevent_switch_stop"] or self.data["set"]["log"][
                                "charged_since_plugged_counter"] == 0) and self.data["config"]["auto_phase_switch_hw"]):
                            phases = 1
                        else:
                            phases = 3
                        log.debug(("Automat. Phasenumschaltung vor Ladestart: Es wird die kleinstmögliche Phasenzahl angenommen. "
                                   f"Phasenzahl: {phases}"))
                else:
                    phases = charging_ev.data["control_parameter"]["phases"]
                    log.debug("Umschaltung wird durchgeführt, Phasenzahl nicht ändern "+str(phases))
            elif chargemode_phases < phases:
                phases = chargemode_phases
                log.debug("Lademodus-Phasen beschränkt die nutzbaren Phasen auf "+str(phases))
            if phases != self.data["get"]["phases_in_use"]:
                # Wenn noch kein Logeintrag erstellt wurde, wurde noch nicht geladen und die Phase kann noch
                # umgeschaltet werden.
                if charging_ev.ev_template.data["prevent_phase_switch"] and self.data["set"]["log"][
                        "imported_since_plugged"] != 0:
                    log.info("Phasenumschaltung an Ladepunkt" + str(self.cp_num) +
                             " nicht möglich, da bei EV " +
                             str(charging_ev.ev_num) +
                             " nach Ladestart nicht mehr umgeschaltet werden darf.")
                    phases = self.data["get"]["phases_in_use"]
                elif self.data["config"]["auto_phase_switch_hw"] is False:
                    log.info("Phasenumschaltung an Ladepunkt" + str(self.cp_num) +
                             " hardwaretechnisch nicht möglich.")
                    phases = self.data["get"]["phases_in_use"]
            if phases != charging_ev.data["control_parameter"]["phases"]:
                charging_ev.data["control_parameter"]["phases"] = phases
                Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/control_parameter/phases", phases)
            return phases
        except Exception:
            log.exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

    def __link_rfid_to_cp(self) -> None:
        """ Wenn der Tag einem EV zugeordnet worden ist, wird der Tag unter set/rfid abgelegt und muss der Timer
        zurückgesetzt werden.
        """
        rfid = self.data["get"]["rfid"]
        self.data["set"]["rfid"] = rfid
        Pub().pub("openWB/chargepoint/"+str(self.cp_num)+"/set/rfid", rfid)
        self.data["get"]["rfid"] = None
        Pub().pub("openWB/chargepoint/"+str(self.cp_num)+"/get/rfid", None)
        self.data["get"]["rfid_timestamp"] = None
        Pub().pub(f"openWB/set/chargepoint/{self.cp_num}/get/rfid_timestamp", None)

    def __validate_rfid(self) -> None:
        """Prüft, dass der Tag an diesem Ladepunkt gültig ist und  dass dieser innerhalb von 5 Minuten einem EV zugeordnet
        wird.
        """
        msg = ""
        if self.data["get"]["rfid"] is not None:
            if data.data.optional_data["optional"].data["rfid"]["active"]:
                rfid = self.data["get"]["rfid"]
                if rfid in self.template.data["valid_tags"] or len(self.template.data["valid_tags"]) == 0:
                    if self.data["get"]["rfid_timestamp"] is None:
                        self.data["get"]["rfid_timestamp"] = timecheck.create_timestamp()
                        Pub().pub(f"openWB/set/chargepoint/{self.cp_num}/get/rfid_timestamp",
                                  self.data["get"]["rfid_timestamp"])
                        return
                    else:
                        if timecheck.check_timestamp(self.data["get"]["rfid_timestamp"], 300):
                            return
                        else:
                            self.data["get"]["rfid_timestamp"] = None
                            Pub().pub(f"openWB/set/chargepoint/{self.cp_num}/get/rfid_timestamp", None)
                            msg = "Es ist in den letzten 5 Minuten kein EV angesteckt worden, dem " \
                                f"der RFID-Tag/Code {rfid} zugeordnet werden kann. Daher wird dieser verworfen."
                else:
                    msg = f"Der Tag {rfid} ist an Ladepunkt {self.cp_num} nicht gültig."
            else:
                msg = "RFID ist nicht aktiviert."
            self.data["get"]["rfid"] = None
            Pub().pub(f"openWB/set/chargepoint/{self.cp_num}/get/rfid", None)
            log.info(f"LP{self.cp_num}: {msg}")
            self.data["get"]["state_str"] = msg


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

    def autolock(self, autolock_state, charge_state, cp_num):
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

        cp_num : str
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
                            "openWB/set/chargepoint/" + str(cp_num) +
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
                "Fehler in der Ladepunkt-Template Klasse von " + str(cp_num))
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
        ev_num: int
            Nummer des zugeordneten EVs, -1 wenn keins zugeordnet werden konnte.
        message: str
            Status-Text
        """
        ev_num = -1
        message = None
        try:
            if data.data.optional_data["optional"].data["rfid"]["active"] and rfid is not None:
                vehicle = ev.get_ev_to_rfid(rfid)
                if vehicle is None:
                    ev_num = -1
                    message = "Keine Ladung, da dem RFID-Tag " + str(rfid)+" kein EV-Profil zugeordnet werden kann."
                else:
                    ev_num = vehicle
            else:
                ev_num = assigned_ev

            return ev_num, message
        except Exception:
            log.exception(
                "Fehler in der Ladepunkt-Template Klasse")
            return ev_num, "Keine Ladung, da ein interner Fehler aufgetreten ist: " + traceback.format_exc()
