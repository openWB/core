"""Ladepunkt-Logik
"""

import time
import RPi.GPIO as GPIO

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

    def used_power_all(self):
        """ermittelt die verwendete Leistung in allen Phasen.

        Return
        ------
        int: aufsummierte Leistung über alle Phasen und Ladepunkte
        """
        try:
            used_power_all = 0
            for chargepoint in data.cp_data:
                if "cp" in chargepoint:
                    if "get" in data.cp_data[chargepoint].data:
                        if "power_all" in data.cp_data[chargepoint].data["get"]:
                            used_power_all += data.cp_data[chargepoint].data["get"]["power_all"]
            data.cp_data["all"].data["get"]["power_all"] = used_power_all
            pub.pub("openWB/set/chargepoint/get/power_all", used_power_all)
        except Exception as e:
            log.exception_logging(e)

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
                            chargepoint.data["set"]["charging_ev"].data["control_parameter"]["chargemode"] != "pv_charging" and 
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
        self.data["set"]["autolock_state"] = 0
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/current", 0)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/autolock_state", 0)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/charging_ev", -1)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/energy_to_charge", 0)
        pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use", 0)

    def _is_cp_available(self):
        """ prüft, ob sich der LP in der vorgegebenen Zeit zurückgemeldet hat.
        """
        # dummy
        state = True
        if state == False:
            message = "LP"+self.cp_num+" gesperrt, da sich der LP nicht innerhalb der vorgegebenen Zeit zurueckgemeldet hat."
        else:
            message = "Ladung an LP"+self.cp_num+" moeglich."
        return state, message

    def _is_autolock_active(self):
        """ ruft die Funktion der Template-Klasse auf.
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

    def _is_manual_lock_active(self):
        state = self.data["set"]["manual_lock"]
        if state == True:
            message = "Keine Ladung an LP"+self.cp_num+", da der LP manuell gesperrt wurde."
        else:
            message = "Ladung an LP"+self.cp_num+" moeglich."
        return state, message

    def _is_ev_plugged(self):
        state = self.data["get"]["plug_state"]
        if state == False:
            message = "Keine Ladung an LP"+self.cp_num+", da kein Auto angesteckt ist."
        else:
            message = "Ladung an LP"+self.cp_num+" moeglich."
        return state, message

    def get_state(self):
        """prüft alle Bedingungen und ruft die EV-Logik auf.

        Return
        ------
        0..x: Nummer des zugeordneten EV
        None: Ladepunkt nicht verfügbar
        """
        try:
            message = "Keine Ladung an LP"+self.cp_num+", da ein Fehler aufgetreten ist."
            charging_possbile = False
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
                self.data["set"]["phases_to_use"] = 0
                pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/phases_to_use", 0)
                return -1, message
        except Exception as e:
            log.exception_logging(e)
            return -1

    def initiate_control_pilot_interruption(self):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = self.data["set"]["charging_ev"]
            # War die Ladung pausiert?
            if self.data["get"]["charge_state"] == False:
                # Ist Control Pilot-Unterbrechung hardwareseitig möglich und ist die Control Pilot-Unterbrechung für das EV erforderlich?
                if self.data["config"]["control_pilot_interruption_hw"] == True and charging_ev.ev_template.data["control_pilot_interruption"] == True:
                # 50s warten bis CP-Skript aufgerufen wird?
                    #self.perform_control_pilot_interruption(charging_ev.ev_template.data["control_pilot_interruption_duration"])
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/perform_control_pilot_interruption", True)
                    log.message_debug_log("debug", "# Control-Pilot-Unterbrechung an LP"+str(self.cp_num)+" fuer "+charging_ev.ev_template.data["control_pilot_interruption_duration"]+"s durchfuehren.")
        except Exception as e:
            log.exception_logging(e)

    def initiate_phase_switch(self, chargepoint):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            if chargepoint.data["config"]["auto_phase_switch_hw"] == True and chargepoint.data["get"]["charge_state"] == True:
                if self.data["get"]["phases_in_use"] != self.data["set"]["phases_to_use"]:
                    #perform hw phase switch
                    pub.pub("openWB/set/chargepoint/"+str(self.cp_num)+"/set/perform_phase_switch", True)
        except Exception as e:
            log.exception_logging(e)

class cpTemplate():
    """ Vorlage für einen LP.
    """

    def __init__(self):
        self.data = {}

    def autolock(self, autolock_state, charge_state, cp_num):
        """ ermittelt den Status des Autolock und published diesen. Es wird sich immer der Status des vorherigen Plans gemerkt, so kann festgestellt  werden, wenn sich zwei Pläne widersprechen.

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
            return True

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