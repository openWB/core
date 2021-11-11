"""Ladepunkt-Logik

charging_ev: EV, das akutell laden darf 
charging_ev_prev: EV, das vorher geladen hat. Dies wird benötigt, da wenn das EV nicht mehr laden darf, z.B. weil Autolock aktiv ist, 
gewartet werden muss, bis die Ladeleistung 0 ist und dann erst der Logeintrag erstellt werden kann. 
charging_ev = -1 zeigt an, dass der LP im Algorithmus nicht berücksichtigt werden soll. 
Ist das Ev abgesteckt, wird auch charging_ev_prev -1 und im nächsten Zyklus kann ein neues Profil geladen werden.

RFID:
Mode 1: Der gescannte Tag  wird dem Ladepunkt zugeordnet, an dem gescannt wude. Falls es eine Duo ist, wird Mode 2 für die beiden Duo-Ladepunkte angewendet.

Freischaltung durch Tag: Aktiviert RFID-Nutzung am Ladepunkt. 
Achtung RFID+Autolock: Ist Autolock aktiviert und der Ladepunkt durch Autolock freigegeben, dient der Tag nur zur EV-Zuordnung.
Ist der Ladepunkt durch Autolock gesperrt, kann er mit einem gültigen Tag freigeschaltet werden.

Zuordnung nur per Tag:
Ist diese Option aktiviert, wird der Tag verworfen, wenn nach 5 Min kein Auto angesteckt wird. Ist diese Option deaktiviert, wird auf das dem Ladepunkt zugeordnete Profil zurück gegriffen. 
Sonst müsste man auch bei Autolock immer einen Tag vorhalten, auch wenn der Ladepunkt durch Autolock freigegeben ist.

RFID-Tags:
Liste der Tags, mit denen der Ladepunkt freigeschaltet werden kann. Ist diese leer, kann mit jedem Tag der Ladepunkt freigeschaltet werden.
"""
import traceback

from . import chargelog
from . import cp_interruption
from . import data
from . import ev
from . import phase_switch
from ..helpermodules import log
from ..helpermodules import pub
from ..helpermodules import timecheck
from ..modules.cp import modbus_evse


def get_chargepoint_default() -> dict:
    return {
        "name": "Standard-Ladepunkt",
        "ev": 0,
        "template": 0,
        "connected_phases": 3,
        "phase_1": 0,
        "auto_phase_switch_hw": False,
        "control_pilot_interruption_hw": False,
        "connection_module":
        {
            "selected": "mqtt"
        },
        "power_module":
        {
            "selected": "mqtt"
        }
    }


class allChargepoints:
    """
    """

    def __init__(self):
        self.data = {"get": {"daily_yield": 0}}
        pub.pub("openWB/set/chargepoint/get/power_all", 0)

    def no_charge(self):
        """ Wenn keine EV angesteckt sind oder keine EV laden/laden möchten, werden die Algorithmus-Werte zurückgesetzt.
        (dient der Robustheit)
        """
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        # Kein EV angesteckt
                        if (chargepoint.data["get"]["plug_state"] is False or
                                # Kein EV, das Laden soll
                                chargepoint.data["set"]["charging_ev"] == -1 or
                                # Kein EV, das auf das Ablaufen der Einschalt- oder Phasenumschaltverzögerung wartet
                                (chargepoint.data["set"]["charging_ev"] != -1 and
                                 chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]["timestamp_perform_phase_switch"] == "0" and
                                 chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]["timestamp_switch_on_off"] == "0")):
                            continue
                        else:
                            break
                except Exception as e:
                    log.MainLogger().exception(
                        "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
            else:
                data.data.pv_data["all"].reset_pv_data()
        except Exception as e:
            log.MainLogger().exception("Fehler in der allgemeinen Ladepunkt-Klasse")

    def get_power_counter_all(self):
        """ ermittelt die aktuelle Leistung und Zählerstand von allen Ladepunkten.
        """
        counter_all = 0
        power_all = 0
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        power_all = power_all + \
                            chargepoint.data["get"]["power_all"]
                        counter_all = counter_all + \
                            chargepoint.data["get"]["counter"]
                except Exception as e:
                    log.MainLogger().exception(
                        "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
            self.data["get"]["power_all"] = power_all
            pub.pub("openWB/set/chargepoint/get/power_all", power_all)
            self.data["get"]["counter_all"] = counter_all
            pub.pub("openWB/set/chargepoint/get/counter_all", counter_all)
        except Exception as e:
            log.MainLogger().exception("Fehler in der allgemeinen Ladepunkt-Klasse")

    def match_rfid_to_cp(self):
        """ ordnet einen gescannten Tag einem Ladepunkt zu. Allgemeine Funktion, da auch an einem zentralen Ladepunkt gescannt werden kann.
        Wenn der RFID-Modus 1 ist, wird die Funktion zur Zuordnung bei zentralem Scanner genutzt, wenn es eine openWB Duo ist. 
        """
        try:
            if data.data.optional_data["optional"].data["rfid"]["active"]:
                # nicht .keys() verwenden, da diese eine dict_keys-Liste erzeugt und wenn man daraus einen Eintrag entfernt wird dieser auch im original-dict entfernt.
                chargepoints = list(data.data.cp_data.keys())
                if "all" in chargepoints:
                    chargepoints.remove("all")
                # Duos zuerst
                for cp in chargepoints:
                    try:
                        chargepoint = data.data.cp_data[cp]
                        if chargepoint.template.data["rfid_enabling"]:
                            # Wurde ein zweiter Ladepunkt an einer Duo konfiguriert?
                            if chargepoint.data["config"]["connection_module"]["selected"] == "external_openwb":
                                if chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["chargepoint"] == 2:
                                    # Ersten Ladepunkt der Duo finden (gleiche IP)
                                    for cp2 in chargepoints:
                                        if cp2 != cp:
                                            if (chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["ip_adress"] ==
                                                    data.data.cp_data[cp2].data["config"]["connection_module"]["config"]["external_openwb"]["ip_adress"]):
                                                self._match_rfid_of_multiple_cp(
                                                    [cp, cp2])
                                                chargepoints.remove(cp)
                                                chargepoints.remove(cp2)
                                                break
                    except Exception as e:
                        log.MainLogger().exception(
                            "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
                # Einzel-Ladepunkte
                for cp in chargepoints:
                    try:
                        if "cp" in cp:
                            chargepoint = data.data.cp_data[cp]
                            if chargepoint.template.data["rfid_enabling"]:
                                if chargepoint.data["get"]["read_tag"]["tag"] != "0":
                                    # Darf mit diesem Tag der LP freigeschaltet werden?
                                    if chargepoint.data["get"]["read_tag"]["tag"] in chargepoint.template.data["valid_tags"] or len(chargepoint.template.data["valid_tags"]) == 0:
                                        chargepoint.data["set"]["rfid"] = chargepoint.data["get"]["read_tag"]["tag"]
                                        pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                                                "/set/rfid", chargepoint.data["set"]["rfid"])
                                        log.MainLogger().info("LP "+str(chargepoint.cp_num)+" wurde Tag " +
                                                              str(chargepoint.data["set"]["rfid"])+" zugeordnet.")
                                    else:
                                        chargepoint.data["get"]["state_str"] = "Tag "+str(
                                            chargepoint.data["get"]["read_tag"]["tag"])+" ist an diesem Ladepunkt nicht gueltig."
                                        log.MainLogger().info("LP "+str(chargepoint.cp_num)+": Tag " +
                                                              str(chargepoint.data["get"]["read_tag"]["tag"])+" ist an diesem Ladepunkt nicht gueltig.")

                                    # Verarbeiteten Tag löschen
                                    chargepoint.data["get"]["read_tag"]["tag"] = "0"
                                    chargepoint.data["get"]["read_tag"]["timestamp"] = "0"
                                    pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                                            "/get/read_tag", chargepoint.data["get"]["read_tag"])
                    except Exception as e:
                        log.MainLogger().exception(
                            "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
        except Exception as e:
            log.MainLogger().exception("Fehler in der allgemeinen Ladepunkt-Klasse")

    def _match_rfid_of_multiple_cp(self, chargepoints):
        """ ordnet einen gescanntem Tag dem Ladepunkt zu, an dem vor / nach dem Scan angesteckt wurde. 

        Parameter
        ---------
        chargepoints: list
            Ladepunkte, denen der Tag zugeordnet werden kann. (nötig für Duo)
        """
        try:
            read_tag = None
            for cp in chargepoints:
                try:
                    if "cp" in cp:
                        chargepoint_read = data.data.cp_data[cp]
                        if chargepoint_read.data["get"]["read_tag"]["tag"] != "0":
                            read_tag = chargepoint_read.data["get"]["read_tag"]["tag"]
                            # Scannen darf nicht länger als 5 Min zurück liegen
                            if timecheck.check_timestamp(chargepoint_read.data["get"]["read_tag"]["timestamp"], 300) is False:
                                # abgelaufen
                                chargepoint_read.data["get"]["read_tag"]["tag"] = "0"
                                chargepoint_read.data["get"]["read_tag"]["timestamp"] = "0"
                                pub.pub("openWB/set/chargepoint/"+str(chargepoint_read.cp_num) +
                                        "/get/read_tag", chargepoint_read.data["get"]["read_tag"])
                except Exception as e:
                    log.MainLogger().exception(
                        "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
            if read_tag is not None:
                last_plugged_cp = None
                plug_time = 0
                for cp in chargepoints:
                    try:
                        if "cp" in cp:
                            chargepoint_match = data.data.cp_data[cp]
                            if chargepoint_match.template.data["rfid_enabling"]:
                                # Wenn man einen Tag hat, der nicht vor mehr als 5 Min gescannt wurde, ist es egal, ob das Auto vor oder nach dem Scannen angesteckt wurde.
                                # Um den Tag zuzuordnen, muss RFID-Zuordnung aktiviert sein, es darf kein Tag zugeordnet sein (wird beim Abstecken zurückgesetzt) und es muss ein Auto angesteckt sein.
                                if chargepoint_match.data["set"]["rfid"] == "0" and chargepoint_match.data["get"]["plug_state"]:
                                    if plug_time == 0 or timecheck.get_difference(plug_time, chargepoint_match.data["set"]["plug_time"]) < 0:
                                        plug_time = chargepoint_match.data["set"]["plug_time"]
                                        last_plugged_cp = chargepoint_match
                    except Exception as e:
                        log.MainLogger().exception(
                            "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
                if last_plugged_cp is None:
                    log.MainLogger().info("Es wurde kein EV angesteckt, dessen Ladepunkt auf eine Zuweisung per RFID wartet. Gescannter Tag: "+str(read_tag))
                else:
                    # Darf mit diesem Tag der LP freigeschaltet werden?
                    if read_tag in last_plugged_cp.template.data["valid_tags"] or len(last_plugged_cp.template.data["valid_tags"]) == 0:
                        last_plugged_cp.data["set"]["rfid"] = read_tag
                        pub.pub("openWB/set/chargepoint/"+str(last_plugged_cp.cp_num) +
                                "/set/rfid", last_plugged_cp.data["set"]["rfid"])
                        log.MainLogger().info("LP "+str(last_plugged_cp.cp_num)+" wurde Tag " +
                                              str(last_plugged_cp.data["set"]["rfid"])+" zugeordnet.")
                        chargepoint_read.data["get"]["read_tag"]["tag"] = "0"
                        chargepoint_read.data["get"]["read_tag"]["timestamp"] = "0"
                        pub.pub("openWB/set/chargepoint/"+str(chargepoint_read.cp_num) +
                                "/get/read_tag", chargepoint_read.data["get"]["read_tag"])
                    else:
                        log.MainLogger().info("Der Tag "+str(read_tag)+" ist an Ladepunkt " +
                                              str(last_plugged_cp.cp_num)+" nicht gueltig.")
                        chargepoint_read.data["get"]["read_tag"]["tag"] = "0"
                        chargepoint_read.data["get"]["read_tag"]["timestamp"] = "0"
                        pub.pub("openWB/set/chargepoint/"+str(chargepoint_read.cp_num) +
                                "/get/read_tag", chargepoint_read.data["get"]["read_tag"])
        except Exception as e:
            log.MainLogger().exception("Fehler in der allgemeinen Ladepunkt-Klasse")

    def check_all_modbus_evse_connections(self):
        try:
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        if chargepoint.data["config"]["connection_module"]["selected"] == "modbus_evse":
                            modbus_evse.check_modbus_evse(chargepoint)
                except Exception as e:
                    log.MainLogger().exception(
                        "Fehler in der allgemeinen Ladepunkt-Klasse fuer Ladepunkt "+cp)
        except Exception as e:
            log.MainLogger().exception("Fehler in der allgemeinen Ladepunkt-Klasse")


class chargepoint:
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf. 
    """

    def __init__(self, index):
        try:
            self.template = None  # Instanz des zugeordneten CP-Templates
            self.cp_num = index
            # set current aus dem vorherigen Zyklus, um zu wissen, ob am Ende des Zyklus die Ladung freigegeben wird (für Control-Pilot-Unterbrechung)
            self.set_current_prev = 0
            # bestehende Daten auf dem Broker nicht zurücksetzen, daher nicht publishen
            self.data = {
                "set": {"charging_ev": -1,
                        "charging_ev_prev": -1,
                        "autolock_state": 0,
                        "current": 0,
                        "energy_to_charge": 0,
                        "plug_time": "0",
                        "rfid": 0,
                        "log": {"counter_at_plugtime": 0,
                                "timestamp_start_charging": "0",
                                "counter_at_mode_switch": 0,
                                "charged_since_mode_switch": 0,
                                "charged_since_plugged_counter": 0,
                                "range_charged": 0,
                                "time_charged": "00:00",
                                "chargemode_log_entry": "_"}},
                "get": {
                    "read_tag": {"tag": "0",
                                 "timestamp": "0"},
                    "daily_yield": 0,
                    "plug_state": False,
                    "charge_state": False,
                    "power_all": 0,
                    "connected_vehicle": {"soc_config": {},
                                          "soc": {},
                                          "info": {},
                                          "config": {}}}}
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

    def _is_grid_protection_inactive(self):
        """ prüft, ob der Netzschutz inaktiv ist oder ob alle Ladepunkt gestoppt werden müssen.

        Return
        ------
        state: bool
            ist Netzschutz inaktiv
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        state = True
        message = None
        try:
            general_data = data.data.general_data["general"].data
            if general_data["grid_protection_configured"]:
                if general_data["grid_protection_active"]:
                    if general_data["grid_protection_timestamp"] != "0":
                        # Timer ist  abglaufen
                        if timecheck.check_timestamp(general_data["grid_protection_timestamp"], general_data["grid_protection_random_stop"]) is False:
                            state = False
                            message = "Ladepunkt gesperrt, da der Netzschutz aktiv ist."
                            pub.pub(
                                "openWB/set/general/grid_protection_timestamp", "0")
                            pub.pub(
                                "openWB/set/general/grid_protection_random_stop", 0)
                    else:
                        state = False
                        message = "Ladepunkt gesperrt, da der Netzschutz aktiv ist."
            return state, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return True, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def _is_ripple_control_receiver_inactive(self):
        """ prüft, dass der Rundsteuerempfängerkontakt nicht geschlossen ist.

        Return
        ------
        state: bool
            ist Netzschutz inaktiv
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        state = True
        message = None
        try:
            general_data = data.data.general_data["general"].data
            if general_data["ripple_control_receiver"]["configured"]:
                if general_data["ripple_control_receiver"]["r1_active"] or general_data["ripple_control_receiver"]["r2_active"]:
                    state = False
                    message = "Ladepunkt gesperrt, da der Rundsteuerempfängerkontakt geschlossen ist."
            return state, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return True, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def _is_loadmanagement_available(self):
        """ prüft, ob Lastmanagement verfügbar ist. Wenn keine Werte vom EVU-Zähler empfangen werden, darf nicht geladen werden.

        Return
        ------
        state: bool
            kann geladen werden
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            if data.data.counter_data["all"].data["set"]["loadmanagement_available"]:
                state = True
                message = None
            else:
                state = False
                message = "Ladepunkt gesperrt, da keine Werte vom EVU-Zähler empfangen wurden und deshalb kein Lastmanagement durchgeführt werden kann. Falls Sie dennoch laden möchten, können Sie als EVU-Zähler 'nicht vorhanden' auswählen und einen konstanten Hausverbrauch angeben."
            return state, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return False, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def _is_autolock_inactive(self):
        """ prüft, ob Autolock nicht aktiv ist oder ob die Sperrung durch einen dem LP zugeordneten RFID-Tag aufgehoben werden kann.

        Return
        ------
        state: bool
            ist Autolock aktiv
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            message = None
            state = self.template.autolock(
                self.data["set"]["autolock_state"], self.data["get"]["charge_state"], self.cp_num)
            if state is False:
                state = True
            else:
                # Darf Autolock durch Tag überschrieben werden?
                if data.data.optional_data["optional"].data["rfid"]["active"] and self.template.data["rfid_enabling"]:
                    if self.data["set"]["rfid"] == "0":
                        state = False
                        message = "Keine Ladung, da der Ladepunkt durch Autolock gesperrt ist und erst per RFID freigeschaltet werden muss."
                    else:
                        state = True
                        message = None
                else:
                    state = False
                    message = "Keine Ladung, da Autolock aktiv ist."
            return state, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return True, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def _is_manual_lock_inactive(self):
        """ prüft, das der Ladepunkt nicht manuell gesperrt wurde.

        Return
        ------
        charging_possbile: bool
            wurde der Ladepunkt gesperrt
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            state = self.data["set"]["manual_lock"]
            if state:
                charging_possbile = False
                message = "Keine Ladung, da der Ladepunkt manuell gesperrt wurde."
            else:
                charging_possbile = True
                message = None
            return charging_possbile, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return True, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def _is_ev_plugged(self):
        """ prüft, ob ein EV angesteckt ist

        Return
        ------
        state: bool
            ist ein EV angesteckt
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            state = self.data["get"]["plug_state"]
            if state is False:
                message = "Keine Ladung, da kein Auto angesteckt ist."
            else:
                log.MainLogger().debug("ev"+str(self.cp_num)+" plugged" +
                                       str(self.data["set"]["plug_time"]))
                if self.data["set"]["plug_time"] == "0":
                    self.data["set"]["plug_time"] = timecheck.create_timestamp()
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num) +
                            "/set/plug_time", self.data["set"]["plug_time"])
                message = None
            return state, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return False, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

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
            message = "Keine Ladung, da ein Fehler aufgetreten ist."
            charging_possbile = False
            state, message = self._is_ev_plugged()
            if state:
                state, message = self._is_grid_protection_inactive()
                if state:
                    state, message = self._is_ripple_control_receiver_inactive()
                    if state:
                        state, message = self._is_loadmanagement_available()
                        if state:
                            state, message = self._is_manual_lock_inactive()
                            if state:
                                charging_possbile, message = self._is_autolock_inactive()
            if charging_possbile:
                ev_num, message = self.template.get_ev(
                    self.data["set"]["rfid"], self.data["config"]["ev"])
                log.MainLogger().debug("possible"+str(ev_num))
                if ev_num != -1:
                    return ev_num, message
                # Tag zurücksetzen, wenn kein EV zugeordnet werden kann
                if self.data["set"]["rfid"] != "0":
                    self.data["set"]["rfid"] = "0"
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num) +
                            "/set/rfid", self.data["set"]["rfid"])
            # Charging Ev ist noch das EV des vorherigen Zyklus, wenn das nicht -1 war und jetzt nicht mehr geladen werden soll (-1), Daten zurücksetzen.
            if self.data["set"]["charging_ev"] != -1:
                # Altes EV merken
                self.data["set"]["charging_ev_prev"] = self.data["set"]["charging_ev"]
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num) +
                        "/set/charging_ev_prev", self.data["set"]["charging_ev_prev"])
            if self.data["set"]["charging_ev_prev"] != -1:
                # Daten zurücksetzen, wenn nicht geladen werden soll.
                data.data.ev_data["ev" +
                                  str(self.data["set"]["charging_ev_prev"])].reset_ev()
                data.data.pv_data["all"].reset_switch_on_off(
                    self, data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])])
                # Abstecken
                if self.data["get"]["plug_state"] is False:
                    # Standardprofil nach Abstecken laden
                    if data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])].charge_template.data["load_default"]:
                        self.data["config"]["ev"] = 0
                        pub.pub("openWB/set/chargepoint/" +
                                str(self.cp_num)+"/config/ev", 0)
                    # Ladepunkt nach Abstecken sperren
                    if data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])].charge_template.data["disable_after_unplug"]:
                        self.data["set"]["manual_lock"] = True
                        pub.pub("openWB/set/chargepoint/" +
                                str(self.cp_num)+"/set/manual_lock", True)
                    # Ev wurde noch nicht aktualisiert.
                    chargelog.reset_data(
                        self, data.data.ev_data["ev"+str(self.data["set"]["charging_ev_prev"])])
                    self.data["set"]["charging_ev_prev"] = -1
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num) +
                            "/set/charging_ev_prev", self.data["set"]["charging_ev_prev"])
                    self.data["set"]["rfid"] = "0"
                    pub.pub("openWB/set/chargepoint/" +
                            str(self.cp_num)+"/set/rfid", "0")
                    self.data["set"]["plug_time"] = "0"
                    pub.pub("openWB/set/chargepoint/" +
                            str(self.cp_num)+"/set/plug_time", "0")
                    self.data["set"]["phases_to_use"] = self.data["get"]["phases_in_use"]
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num) +
                            "/set/phases_to_use", self.data["set"]["phases_to_use"])
            self.data["set"]["charging_ev"] = -1
            pub.pub("openWB/set/chargepoint/" +
                    str(self.cp_num)+"/set/charging_ev", -1)
            self.data["set"]["current"] = 0
            pub.pub("openWB/set/chargepoint/" +
                    str(self.cp_num)+"/set/current", 0)
            self.data["set"]["energy_to_charge"] = 0
            pub.pub("openWB/set/chargepoint/" +
                    str(self.cp_num)+"/set/energy_to_charge", 0)
            return -1, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))
            return -1, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def initiate_control_pilot_interruption(self):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data["set"]["charging_ev_data"]
            # Unterstützt der Ladepunkt die CP-Unterbrechung und benötigt das Auto eine CP-Unterbrechung?
            if self.data["config"]["control_pilot_interruption_hw"] and charging_ev.ev_template.data["control_pilot_interruption"]:
                # Wird die Ladung gestartet?
                if self.set_current_prev == 0 and self.data["set"]["current"] != 0:
                    selected = self.data["config"]["connection_module"]["selected"]
                    config = self.data["config"]["connection_module"]["config"][selected]
                    #cp_interruption.thread_cp_interruption(self.cp_num, selected, config, charging_ev.ev_template.data["control_pilot_interruption_duration"])
                    message = "Control-Pilot-Unterbrechung fuer " + \
                        str(
                            charging_ev.ev_template.data["control_pilot_interruption_duration"])+"s."
                    log.MainLogger().info("LP "+str(self.cp_num)+": "+message)
                    self.data["get"]["state_str"] = message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

    def initiate_phase_switch(self):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data["set"]["charging_ev_data"]
            # Umschaltung im Gange
            if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] != "0":
                phase_switch_pause = charging_ev.ev_template.data["phase_switch_pause"]
                # Umschaltung abgeschlossen
                if timecheck.check_timestamp(charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"], 6+phase_switch_pause-1) is False:
                    log.MainLogger().debug("phase switch running")
                    charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] = "0"
                    pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                            "/control_parameter/timestamp_perform_phase_switch", "0")
                    # Aktuelle Ladeleistung und Differenz wieder freigeben.
                    if charging_ev.data["control_parameter"]["phases"] == 3:
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= charging_ev.data["control_parameter"]["required_current"] * 3 * 230
                    elif charging_ev.data["control_parameter"]["phases"] == 1:
                        data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= charging_ev.ev_template.data["max_current_one_phase"] * 230
                else:
                    # Wenn eine Umschaltung im Gange ist, muss erst gewartet werden, bis diese fertig ist.
                    if self.data["set"]["phases_to_use"] == 3:
                        message = "Umschaltung von 1 auf 3 Phasen."
                    elif self.data["set"]["phases_to_use"] == 1:
                        message = "Umschaltung von 3 auf 1 Phase."
                    else:
                        raise ValueError(
                            str(self.data["set"]["phases_to_use"])+" ist keine gültige Phasenzahl (1/3).")
                    self.data["get"]["state_str"] = message
                return
            # Wenn noch kein Logeintrag erstellt wurde, wurde noch nicht geladen und die Phase kann noch umgeschaltet werden.
            if charging_ev.ev_template.data["prevent_switch_stop"] is False or self.data["set"]["log"]["charged_since_plugged_counter"] == 0:
                # Einmal muss die Anzahl der Phasen gesetzt werden.
                if "phases_to_use" not in self.data["set"]:
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use",
                            charging_ev.data["control_parameter"]["phases"])
                    self.data["set"]["phases_to_use"] = charging_ev.data["control_parameter"]["phases"]
                # Manche EVs brauchen nach der Umschaltung mehrere Zyklen, bis sie mit den drei Phasen laden. Dann darf nicht zwischendurch eine neue Umschaltung getriggert werden.
                if (self.data["set"]["phases_to_use"] != charging_ev.data["control_parameter"]["phases"] and self.data["set"]["log"]["charged_since_mode_switch"] > 0 or
                        self.data["get"]["phases_in_use"] != charging_ev.data["control_parameter"]["phases"] and self.data["set"]["log"]["charged_since_mode_switch"] == 0):
                    # Wenn die Umschaltverzögerung aktiv ist, darf nicht umgeschaltet werden.
                    if charging_ev.data["control_parameter"]["timestamp_auto_phase_switch"] == "0":
                        if self.data["config"]["auto_phase_switch_hw"]:
                            selected = self.data["config"]["connection_module"]["selected"]
                            config = self.data["config"]["connection_module"]["config"][selected]
                            charge_state = self.data["get"]["charge_state"]
                            phase_switch.thread_phase_switch(
                                self.cp_num, selected, config, charging_ev.data["control_parameter"]["phases"], charging_ev.ev_template.data["phase_switch_pause"], charge_state)
                            log.MainLogger().debug("start phase switch phases_to_use " +
                                                   str(self.data["set"]["phases_to_use"])+"control_parameter phases "+str(charging_ev.data["control_parameter"]["phases"]))
                            # 1 -> 3
                            if charging_ev.data["control_parameter"]["phases"] == 3:
                                message = "Umschaltung von 1 auf 3 Phasen."
                                log.MainLogger().info("LP "+str(self.cp_num)+": "+message)
                                self.data["get"]["state_str"] = message
                                # Timestamp für die Durchführungsdauer
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] += charging_ev.data["control_parameter"]["required_current"] * 3 * 230
                                charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] = timecheck.create_timestamp(
                                )
                                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num) + "/control_parameter/timestamp_perform_phase_switch",
                                        charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"])
                            elif charging_ev.data["control_parameter"]["phases"] == 1:
                                message = "Umschaltung von 3 auf 1 Phase."
                                # Timestamp für die Durchführungsdauer
                                charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] = timecheck.create_timestamp(
                                )
                                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num) + "/control_parameter/timestamp_perform_phase_switch",
                                        charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"])
                                # Ladeleistung reservieren, da während der Umschaltung die Ladung pausiert wird.
                                data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] += charging_ev.ev_template.data["max_current_one_phase"] * 230
                                log.MainLogger().info("LP "+str(self.cp_num)+": "+message)
                                self.data["get"]["state_str"] = message
                        else:
                            log.MainLogger().error("Phasenumschaltung an Ladepunkt"+str(self.cp_num) +
                                                   " nicht möglich, da der Ladepunkt keine Phasenumschaltung unterstützt.")
                    else:
                        log.MainLogger().error("Phasenumschaltung an Ladepunkt"+str(self.cp_num) +
                                               " nicht möglich, da gerade eine Umschaltung im Gange ist.")
            if self.data["set"]["phases_to_use"] != charging_ev.data["control_parameter"]["phases"]:
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use",
                        charging_ev.data["control_parameter"]["phases"])
                self.data["set"]["phases_to_use"] = charging_ev.data["control_parameter"]["phases"]
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))

    def get_phases(self, mode):
        """ ermittelt die maximal mögliche Anzahl Phasen, die von Konfiguration, Auto und Ladepunkt unterstützt wird und prüft anschließend, ob sich die Anzahl der genutzten Phasen geändert hat.

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
            else:
                phases = config["connected_phases"]
            log.MainLogger().debug("phases1 "+str(phases))
            chargemode_phases = data.data.general_data["general"].get_phases_chargemode(
                mode)
            # Wenn die Lademodus-Phasen 0 sind, wird die bisher genutzte Phasenzahl weiter genutzt,
            # bis der Algorithmus eine Umschaltung vorgibt, zB weil der gewählte Lademodus eine
            # andere Phasenzahl benötigt oder bei PV-Laden die automatische Umschaltung aktiv ist.
            if chargemode_phases == 0:
                log.MainLogger().debug("timestamp_perform_phase_switch "+str(charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"]) +
                                       "control_parameter phases "+str(charging_ev.data["control_parameter"]["phases"])+"phases_in_use "+str(self.data["get"]["phases_in_use"]))
                charging_ev.data["control_parameter"]["phases"] = self.data["get"]["phases_in_use"]
                if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] == "0":
                    if self.data["get"]["phases_in_use"] == 1:
                        phases = 1
                    else:
                        phases = 3
                else:
                    phases = charging_ev.data["control_parameter"]["phases"]
            elif chargemode_phases < phases:
                phases = chargemode_phases
            log.MainLogger().debug("chargemode_phases "+str(chargemode_phases))
            log.MainLogger().debug("phases "+str(phases))
            # Wenn noch kein Logeintrag erstellt wurde, wurde noch nicht geladen und die Phase kann noch umgeschaltet werden.
            if charging_ev.ev_template.data["prevent_switch_stop"] and self.data["set"]["log"]["charged_since_plugged_counter"] != 0:
                log.MainLogger().info("Phasenumschaltung an Ladepunkt"+str(self.cp_num)+" nicht möglich, da bei EV " +
                                      str(charging_ev.ev_num)+" nach Ladestart nicht mehr umgeschaltet werden darf.")
                phases = self.data["get"]["phases_in_use"]
            if phases != charging_ev.data["control_parameter"]["phases"]:
                charging_ev.data["control_parameter"]["phases"] = phases
                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                        "/control_parameter/phases", phases)
            return phases
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Klasse von "+str(self.cp_num))


def get_chargepoint_template_default():
    return {
        "name": "Standard Ladepunkt-Vorlage",
        "autolock": {
            "wait_for_charging_end": False,
            "active": False},
        "rfid_enabling": False,
        "valid_tags": ["1234"]
    }


def get_autolock_plan_default():
    return {
        "name": "Standard Autolock-Plan",
        "frequency":
        {
            "selected": "daily",
            "once": ["2021-11-01", "2021-11-05"],
            "weekly": [False, False, False, False, False, False, False]
        },
        "time": ["07:00", "16:00"],
        "active": True
    }


class cpTemplate:
    """ Vorlage für einen Ladepunkt.
    """

    def __init__(self):
        self.data = {}

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
        True: nicht durch Autolock gesperrt -> Ladung möglich
        False: durch Autolock gesperrt
        """
        try:
            if (self.data["autolock"]["active"]):
                if autolock_state != 4:
                    if timecheck.check_plans_timeframe(self.data["autolock"]["plans"]) is not None:
                        if self.data["autolock"]["wait_for_charging_end"]:
                            if charge_state:
                                state = 1
                            else:
                                state = 2
                        else:
                            state = 2
                    else:
                        state = 3

                    pub.pub("openWB/set/chargepoint/"+str(cp_num) +
                            "/set/autolock_state", state)
                    if (state == 1) or (state == 3):
                        return False
                    elif state == 2:
                        return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Template Klasse von "+str(cp_num))
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
                pub.pub(topic_path+"/get/autolock", 4)
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Template Klasse")

    def autolock_manual_enabling(self, topic_path):
        """ aktuelles Autolock wird wieder aktiviert.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"]):
                pub.pub(topic_path+"/get/autolock", 0)
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Template Klasse")

    def autolock_enable_after_charging_end(self, autolock_state, topic_path):
        """Wenn kein Strom für den Ladepunkt übrig ist, muss Autolock ggf noch aktiviert werden.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"]) and autolock_state == 1:
                pub.pub(topic_path+"/set/autolock", 2)
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Template Klasse")

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
            if (data.data.optional_data["optional"].data["rfid"]["active"]
                    and self.data["rfid_enabling"]
                    and rfid != "0"):
                vehicle = ev.get_ev_to_rfid(rfid)
                if vehicle is None:
                    ev_num = -1
                    message = "Keine Ladung, da dem RFID-Tag " + \
                        str(rfid)+" kein EV-Profil zugeordnet werden kann."
                else:
                    ev_num = vehicle
            else:
                ev_num = assigned_ev

            return ev_num, message
        except Exception as e:
            log.MainLogger().exception("Fehler in der Ladepunkt-Template Klasse")
            return ev_num, "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()
