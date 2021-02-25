""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.
"""

import data
import timecheck

class ev():
    """Logik des EV
    """

    def __init__(self):
        self.data={}
        self.ev_template=0
        self.charge_template=0
        
    def get_required_current(self):
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)
        """
        if data.ev_charge_template_data[self.charge_template].time_load == True:
            self.__time_load()
        if data.ev_charge_template_data[self.charge_template].charge_mode == "instant_load":
            self.__instant_load()
        elif data.ev_charge_template_data[self.charge_template].charge_mode == "pv_load":
            self.__pv_load()
        elif data.ev_charge_template_data[self.charge_template].charge_mode == "scheduled_load":
            self.__scheduled_load()

        self.__check_min_current()
    

    def get_soc(self):
        """ermittelt den SoC, wenn die Zugangsdaten konfiguriert sind.
        """
        pass

    def __pv_load(self):
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.
        """
        pass

    def __instant_load(self):
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.
        """
        pass

    def __scheduled_load(self):
        """ prüft, ob der Ziel-SoC erreicht wurde und stellt den zur Erreichung nötigen Ladestrom ein.
        """
        pass

    def __check_min_current(self):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom des EVs liegt. Falls nicht, wird der 
        Ladestrom auf den Mindest-Ladestrom des EV gesetzt.
        """
        pass

    def load_default_profile(self):
        """ prüft, ob nach dem Abstecken das Standardprofil geladen werden soll und lädt dieses ggf..
        """
        pass

    def lock_cp(self):
        """prüft, ob nach dem Abstecken der LP gesperrt werden soll und sperrt diesen ggf..
        """
        pass
        

class evTemplate():
    """ Klasse mit den EV-Daten
    """

    def __init__(self):
        self.data={}

class chargeTemplate():
    """ Klasse der Lademodus-Vorlage
    """

    def __init__(self):
        self.data={}

    def __time_load(self):
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        try:
            if self.data["time_load"]["active"] == True:
                for plan in self.data["time_load"]:
                    try:
                        if "plan" in plan:
                            if timecheck.check_timeframe(plan) == True:
                                return plan["current"]
                            else:
                                None
                    except:
                            print("dictionary key related to loop-object", plan, "doesn't exist in __time_load")
        except:
            print("dictionary key doesn't exist in __time_load")


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
    for vehicle in data.ev_data:
        if ("ev" in vehicle) or ("default"==vehicle):
            try:
                if data.ev_data[vehicle].data["match_ev"]["selected"] == "rfid":
                    if data.ev_data[vehicle].data["match_ev"]["tag_id"] == rfid:
                        if vehicle == "default":
                            return 0
                        else:
                            return int(vehicle[2:])
            except:
                print("dictionary key related to loop-object", vehicle, "doesn't exist in get_ev_to_rfid")
    else:
        return None
    
