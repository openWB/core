"""Ladepunkt-Logik
"""

import data
import ev
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
        self.topic_path = None

    def __is_cp_available(self):
        """ prüft, ob sich der LP in der vorgegebenen Zeit zurückgemeldet hat.
        """
        # dummy
        return True

    def __is_autolock_active(self):
        """ ruft die Funktion der Template-Klasse auf.
        """
        try:
            return self.template.autolock(self.data["get"]["autolock_state"], self.data["get"]["charge_state"], self.topic_path)
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in __is_autolock_active")

    def get_state(self):
        """prüft alle Bedingungen und ruft die EV-Logik auf.

        Return
        ------
        0..x: Nummer des zugeordneten EV
        None: Ladepunkt nicht verfügbar
        """
        try:
            if self.__is_cp_available() == True:
                if self.data["get"]["manual_lock"] == False:
                    if self.data["get"]["plug_state"] == True:
                        if self.__is_autolock_active() == True:
                            return self.template.get_ev(self.data["get"]["rfid"])
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_state")
            return None
        return None

    def set_template(self):
        """ setzt die Instanz des zugeordneten Templates als Attribut.
        """
        try:
            self.template = data.cp_template_data["cpt" +
                                                  str(self.data["config"]["template"])]
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in set_template")

    def set_topic_path(self, chargepoint_num):
        """ setzt den Pfad zum Publishen der Topics.

        Paramter
        --------
        chargepoint_num : int
            Ladepunkt-Nummer
        """
        self.topic_path = "openWB/chargepoint/"+chargepoint_num


class cpTemplate():
    """ Vorlage für einen LP.
    """

    def __init__(self):
        self.data = {}

    def autolock(self, autolock_state, charge_state, topic_path):
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

        topic_path : str
            allgemeiner Pfad für Chargepoint-Topics

        Return
        ------
        True: nicht durch Autolock gesperrt -> Ladung möglich
        False: durch Autolock gesperrt
        """
        try:
            if (self.data["autolock"]["active"] == True):
                if autolock_state != 4:
                    if timecheck.check_timeframe(self.data["autolock"]) != None:
                        if self.data["autolock"]["wait_for_charging_end"] == True:
                            if charge_state == True:
                                state = 1
                            else:
                                state = 2
                        else:
                            state = 2
                    else:
                        state = 3

                    pub.pub(topic_path+"/get/autolock_state", state)
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