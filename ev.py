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
        self.ev_template=None
        self.charge_template=None
    
    def set_templates(self):
        """ setzt die Instanz des zugeordneten Templates als Attribut.
        """
        try:
            self.ev_template = data.ev_template_data["et" + str(self.data["ev_template"])]
            self.charge_template = data.ev_charge_template_data["ct" + str(self.data["charge_template"])]
        except:
            print("dictionary key doesn't exist in set_templates")

        
    def get_required_current(self):
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)

        Return
        ------
        required_current: int
            Strom, der nach Ladekonfiguration benötigt wird
        """
        try:
            if self.charge_template.data["time_load"]["active"] == True:
                return self.charge_template.time_load()
                # if data.ev_charge_template_data[self.charge_template].charge_mode == "instant_load":
                #     self.__instant_load()
                # elif data.ev_charge_template_data[self.charge_template].charge_mode == "pv_load":
                #     self.__pv_load()
                # elif data.ev_charge_template_data[self.charge_template].charge_mode == "scheduled_load":
                #     self.__scheduled_load()

                # self.__check_min_current()
        except:
            print("dictionary key doesn't exist in get_required_current")
    

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

    def time_load(self):
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        try:
            if self.data["time_load"]["active"] == True:
                plan = timecheck.check_timeframe(self.data["time_load"])
                if plan != None:
                    return self.data["time_load"][plan]["current"]
                else:
                    return 0
        except:
            print("dictionary key doesn't exist in time_load")


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
    
