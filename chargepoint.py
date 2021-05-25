"""Ladepunkt-Logik
"""

import data
import ev
import log
import pub
import timecheck


class allChargepoints():
    """
    """

    def __init__(self):
        self.data = {}
        self.data["get"] = {}
        pub.pub("openWB/set/chargepoint/get/power_all", 0)

    def no_charge(self):
        """ Wenn keine EV angesteckt sind oder keine EV laden/laden möchten, werden die Algorithmus-Werte zurückgesetzt.
        (dient der Robustheit)
        """
        try:
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    # Kein EV angesteckt
                    if ( chargepoint.data["get"]["plug_state"] == False or
                            # Kein EV, das Laden soll
                            chargepoint.data["set"]["charging_ev"] == -1 or 
                            # Kein EV, das auf das Ablaufen der Einschaltverzögerung wartet
                            (chargepoint.data["set"]["charging_ev"] != -1 and 
                            chargepoint.data["set"]["charging_ev"].data["control_parameter"]["submode"] != "pv_charging" and 
                            chargepoint.data["get"]["charge_state"] == False)):
                        continue
                    else:
                        break
            else:
                data.pv_data["all"].reset_pv_data()
        except Exception as e:
            log.exception_logging(e)



class chargepoint():
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf. 
    """

    def __init__(self, index):
        self.data = {}
        self.template = None  # Instanz des zugeordneten CP-Templates
        self.cp_num = index
        self.data["set"] = {}
        self.set_current_prev = 0 # set current aus dem vorherigen Zyklus, um zu wissen, ob am Ende des Zyklus die Ladung freigegeben wird (für Control-Pilot-Unterbrechung)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/current", 0)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/autolock_state", 0)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/charging_ev", -1)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/energy_to_charge", 0)
        self.data["set"]["charging_ev"] = -1
        self.data["set"]["autolock_state"] = 0
        self.data["set"]["current"] = 0
        self.data["set"]["energy_to_charge"] = 0

    def _is_grid_protection_active(self):
        """ prüft, ob der Netzschutz aktiv ist und alle LP gestoppt werden müssen.

        Return
        ------
        state: bool
            ist Netzschutz aktiv
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            if data.general_data["general"].data["grid_protection_configured"] == True:
                if data.general_data["general"].data["grid_protection_active"] == False:
                    state = False
                    message = "Ladung an LP"+self.cp_num+" moeglich."
                else:
                    state = True
                    message = "LP"+self.cp_num+" gesperrt, da der Netzschutz aktiv ist."
            else:
                state = False
                message = "Ladung an LP"+self.cp_num+" moeglich."
            return state, message
        except Exception as e:
            log.exception_logging(e)
            return True, "Keine Ladung an LP"+self.cp_num+", da ein interner Fehler aufgetreten ist."

    def _is_cp_available(self):
        """ prüft, ob sich der LP in der vorgegebenen Zeit zurückgemeldet hat.

        Return
        ------
        state: bool
            kann geladen werden
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            if True:
            #if self.data["get"]["fault_state"] == 0:
                state = True
                message = "Ladung an LP"+self.cp_num+" moeglich."
            else:
                state = False
                message = "LP"+self.cp_num+" gesperrt, da sich der LP nicht innerhalb der vorgegebenen Zeit zurueckgemeldet hat."
            return state, message
        except Exception as e:
            log.exception_logging(e)
            return False, "Keine Ladung an LP"+self.cp_num+", da ein interner Fehler aufgetreten ist."

    def _is_autolock_active(self):
        """ ruft die Funktion der Template-Klasse auf.

        Return
        ------
        state: bool
            ist Autolock aktiv
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            state = self.template.autolock(self.data["set"]["autolock_state"], self.data["get"]["charge_state"], self.cp_num)
            if state == True:
                message = "Keine Ladung an LP"+self.cp_num+", da Autolock aktiv ist."
            else:
                message = "Ladung an LP"+self.cp_num+" moeglich."
            return state, message
        except Exception as e:
            log.exception_logging(e)
            return True, "Keine Ladung an LP"+self.cp_num+", da ein interner Fehler aufgetreten ist."

    def _is_manual_lock_active(self):
        """ prüft, ob der Ladepunkt manuell gesperrt wurde.

        Return
        ------
        state: bool
            wurde der Ladepunkt gesperrt
        message: str
            Text, dass geladen werden kann oder warum nicht geladen werden kann.
        """
        try:
            state = self.data["set"]["manual_lock"]
            if state == True:
                message = "Keine Ladung an LP"+self.cp_num+", da der LP manuell gesperrt wurde."
            else:
                message = "Ladung an LP"+self.cp_num+" moeglich."
            return state, message
        except Exception as e:
            log.exception_logging(e)
            return True, "Keine Ladung an LP"+self.cp_num+", da ein interner Fehler aufgetreten ist."

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
            if state == False:
                message = "Keine Ladung an LP"+self.cp_num+", da kein Auto angesteckt ist."
            else:
                message = "Ladung an LP"+self.cp_num+" moeglich."
            return state, message
        except Exception as e:
            log.exception_logging(e)
            return False, "Keine Ladung an LP"+self.cp_num+", da ein interner Fehler aufgetreten ist."

    def get_state(self):
        """prüft alle Bedingungen und ruft die EV-Logik auf.

        Return
        ------
        0..x: Nummer des zugeordneten EV
        None: Ladepunkt nicht verfügbar
        """
        try:
            # Für Control-Pilot-Unterbrechung set current merken.
            if "current" not in self.data["set"]:
                self.set_current_prev = 0
            else:
                self.set_current_prev = self.data["set"]["current"]
            message = "Keine Ladung an LP"+self.cp_num+", da ein Fehler aufgetreten ist."
            charging_possbile = False
            state, message = self._is_grid_protection_active()
            if state == False:
                state, message = self._is_cp_available()
                if state == True:
                    state, message = self._is_manual_lock_active()
                    if state == False:
                        state, message = self._is_ev_plugged()
                        if state == True:
                            state, message = self._is_autolock_active()
                            if state == False:
                                charging_possbile = True
                    
            if charging_possbile == True:
                return self.template.get_ev(self.data["get"]["rfid"], self.cp_num), message
            else:
                # Daten zurücksetzen, wenn nicht geladen werden soll.
                if self.data["set"]["charging_ev"] != -1:
                    if  "timestamp_switch_on_off" in data.ev_data["ev"+str(self.data["set"]["charging_ev"])].data["control_parameter"]:
                        if data.ev_data["ev"+str(self.data["set"]["charging_ev"])].data["control_parameter"]["timestamp_switch_on_off"] != "0":
                            if self.data["get"]["charge_state"] == False:
                                data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= self.data["set"]["required_power"]
                            else:
                                data.pv_data["all"].data["set"]["released_evu_overhang"] -= self.data["set"]["required_power"] 
                    data.ev_data["ev"+str(self.data["set"]["charging_ev"])].reset_ev()
                self.data["set"]["charging_ev"] = -1
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/charging_ev", -1)
                self.data["set"]["current"] = 0
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/current", 0)
                self.data["set"]["energy_to_charge"] = 0
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/energy_to_charge", 0)
                return -1, message
        except Exception as e:
            log.exception_logging(e)
            return -1

    def initiate_control_pilot_interruption(self):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data["set"]["charging_ev"]
            # Unterstützt der LP die CP-Unterbrechung und benötigt das Auto eine CP-Unterbrechung?
            if self.data["config"]["control_pilot_interruption_hw"] == True and charging_ev.ev_template.data["control_pilot_interruption"] == True:
                # Wird die Ladung gestartet?
                if self.set_current_prev == 0 and self.data["set"]["current"] != 0:
                    self.data["set"]["perform_control_pilot_interruption"] = charging_ev.ev_template.data["control_pilot_interruption_duration"]
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/perform_control_pilot_interruption", charging_ev.ev_template.data["control_pilot_interruption_duration"])
                    log.message_debug_log("debug", "Control-Pilot-Unterbrechung an LP"+str(self.cp_num)+" fuer "+str(charging_ev.ev_template.data["control_pilot_interruption_duration"])+"s angestoßen.")
        except Exception as e:
            log.exception_logging(e)

    def initiate_phase_switch(self):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            # Einmal muss die Anzahl der Phasen gesetzt werden.
            if "phases_to_use" not in self.data["set"]:
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use", self.data["set"]["charging_ev"].data["control_parameter"]["phases"])
                self.data["set"]["phases_to_use"] = self.data["set"]["charging_ev"].data["control_parameter"]["phases"]
            if self.data["set"]["phases_to_use"] != self.data["set"]["charging_ev"].data["control_parameter"]["phases"]:
                if self.data["config"]["auto_phase_switch_hw"] == True and self.data["get"]["charge_state"] == True:
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use", self.data["set"]["charging_ev"].data["control_parameter"]["phases"])
                else:
                    log.message_debug_log("error", "Phasenumschaltung an LP"+str(self.cp_num)+" nicht möglich.")
        except Exception as e:
            log.exception_logging(e)

    def get_phases(self):
        """ ermittelt die maximal mögliche Anzahl Phasen, die von Konfiguration, Auto und Ladepunkt unterstützt wird und prüft anschließend, ob sich die Anzahl der genutzten Phasen geändert hat.

        Return
        ------
        phases: int
            Anzahl Phasen
        """
        try:
            phases = 0
            charging_ev = self.data["set"]["charging_ev"]
            config = self.data["config"]
            if charging_ev.ev_template.data["max_phases"] <= config["connected_phases"]:
                phases = charging_ev.ev_template.data["max_phases"]
            else:
                phases = config["connected_phases"]
            chargemode = charging_ev.data["control_parameter"]["submode"]
            chargemode_phases = data.general_data["general"].get_phases_chargemode(chargemode)
            if chargemode_phases == 0:
                if self.data["set"]["current"] == 0:
                # Im Automatik-Modus muss die Ladung mit einer Phase begonnen werden.
                    phases = 1
                else:
                    phases = charging_ev.data["control_parameter"]["phases"]
            elif chargemode_phases < phases:
                phases = chargemode_phases
            if phases != charging_ev.data["control_parameter"]["phases"]:
                charging_ev.data["control_parameter"]["phases"] = phases
                pub.pub("openWB/set/vehicle/"+str(charging_ev.ev_num)+"/control_parameter/phases", phases)
        except Exception as e:
            log.exception_logging(e)

class cpTemplate():
    """ Vorlage für einen LP.
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
            LP-Nummer

        Return
        ------
        True: nicht durch Autolock gesperrt -> Ladung möglich
        False: durch Autolock gesperrt
        """
        try:
            if (self.data["autolock"]["active"] == True):
                if autolock_state != 4:
                    if timecheck.check_plans_timeframe(self.data["autolock"]) != None:
                        if self.data["autolock"]["wait_for_charging_end"] == True:
                            if charge_state == True:
                                state = 1
                            else:
                                state = 2
                        else:
                            state = 2
                    else:
                        state = 3

                    pub.pub("openWB/set/chargepoint/"+cp_num+"/set/autolock_state", state)
                    if (state == 1) or (state == 3):
                        return False
                    elif state == 2:
                        return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            log.exception_logging(e)
            return False

    def autolock_manual_disabling(self, topic_path):
        """ aktuelles Autolock wird außer Kraft gesetzt.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"] == True):
                pub.pub(topic_path+"/get/autolock", 4)
        except Exception as e:
            log.exception_logging(e)

    def autolock_manual_enabling(self, topic_path):
        """ aktuelles Autolock wird wieder aktiviert.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"] == True):
                pub.pub(topic_path+"/get/autolock", 0)
        except Exception as e:
            log.exception_logging(e)

    def autolock_enable_after_charging_end(self, autolock_state, topic_path):
        """Wenn kein Strom für den LP übrig ist, muss Autolock ggf noch aktiviert werden.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"] == True) and autolock_state == 1:
                pub.pub(topic_path+"/set/autolock", 2)
        except Exception as e:
            log.exception_logging(e)

    def get_ev(self, rfid, cp_num):
        """ermittelt das dem LP zugeordnete EV
        """
        ev_num = -1
        try:
            if self.data["rfid_enabling"] == True and rfid != 0:
                vehicle = ev.get_ev_to_rfid(rfid)
                if vehicle == None:
                    ev_num = self.data["ev"]
                else:
                    ev_num = vehicle
            else:
                ev_num = self.data["ev"]
            pub.pub("openWB/set/chargepoint/"+cp_num+"/set/charging_ev", ev_num)
            return ev_num
        except Exception as e:
            log.exception_logging(e)
            return ev_num