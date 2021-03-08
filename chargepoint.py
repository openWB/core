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


class chargepoint():
    """ geht alle Ladepunkte durch, prüft, ob geladen werden darf und ruft die Funktion des angesteckten Autos auf. 
    """

    def __init__(self):
        self.data = {}
        self.template = None  # Instanz des zugeordneten CP-Templates
        self.cp_num = None
        self.data["get"] = {}
        self.data["get"]["autolock_state"] = 0
        self.data["get"]["charge_state"] = 0
        self.data["set"] = {}

    def log_pub_state_str(self, message):
        """sendet die Nachricht an den Broker und schreibt sie ins Debug-Log

        Parameter
        ---------
        message: str
            Nachricht, die gesendet werden soll
        """
        log.message_debug_log("info", message)
        pub.pub("openWB/chargepoint/"+self.cp_num+"/get/state_str", message)

    def _is_cp_available(self):
        """ prüft, ob sich der LP in der vorgegebenen Zeit zurückgemeldet hat.
        """
        # dummy
        state = True
        if state == False:
            self.log_pub_state_str("LP"+self.cp_num+" gesperrt, da sich der LP nicht innerhalb der vorgegebenen Zeit zurueckgemeldet hat.")
        return state

    def _is_autolock_active(self):
        """ ruft die Funktion der Template-Klasse auf.
        """
        try:
            state = self.template.autolock(self.data["get"]["autolock_state"], self.data["get"]["charge_state"], self.cp_num)
            if state == False:
                self.log_pub_state_str("Keine Ladung an LP"+self.cp_num+", da Autolock aktiv ist.")
            return state
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in __is_autolock_active")

    def _is_manual_lock_active(self):
        state = self.data["get"]["manual_lock"]
        if state == True:
            self.log_pub_state_str("Keine Ladung an LP"+self.cp_num+", da der LP manuell gesperrt wurde.")
            print(state)
        return state

    def _is_ev_plugged(self):
        state = self.data["get"]["plug_state"]
        if state == False:
            self.log_pub_state_str("Keine Ladung an LP"+self.cp_num+", da kein Auto angesteckt ist.")
        return state

    def get_state(self):
        """prüft alle Bedingungen und ruft die EV-Logik auf.

        Return
        ------
        0..x: Nummer des zugeordneten EV
        None: Ladepunkt nicht verfügbar
        """
        try:
            if self._is_cp_available() == True:
                if self._is_manual_lock_active() == False:
                    if self._is_ev_plugged() == True:
                        if self._is_autolock_active() == True:
                            return self.template.get_ev(self.data["get"]["rfid"])
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_state")
            return None
        return None


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

                    pub.pub("openWB/chargepoint/"+cp_num+"/get/autolock_state", state)
                    if (state == 1) or (state == 3):
                        return True
                    elif state == 2:
                        return False
                else:
                    return True
            else:
                return True
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in autolock")
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
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in autolock_manual_disabling")

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
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in autolock_manual_enabling")

    def autolock_enable_after_charging_end(self, autolock_state, topic_path):
        """Wenn kein Strom für den LP übrig ist, muss Autolock ggf noch aktiviert werden.

        Parameter
        ---------
        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics
        """
        try:
            if (self.data["autolock"]["active"] == True) and autolock_state == 1:
                pub.pub(topic_path+"/get/autolock", 2)
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in autolock_enable_after_charging_end")

    def get_ev(self, rfid):
        """ermittelt das dem LP zugeordnete EV
        """
        try:
            if self.data["rfid_enabling"] == True and rfid != 0:
                vehicle = ev.get_ev_to_rfid(rfid)
                if vehicle == None:
                    return self.data["ev"]
                else:
                    return vehicle
            else:
                return self.data["ev"]
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_ev")