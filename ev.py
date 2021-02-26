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
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in set_templates")

        
    def get_required_current(self):
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)

        Return
        ------
        required_current: int
            Strom, der nach Ladekonfiguration benötigt wird
        """
        try:
            if "set" not in self.data:
                self.data["set"] = {}
            if self.charge_template.data["time_load"]["active"] == True:
                self.data["set"]["required_current"] = self.charge_template.time_load()
                self.data["set"]["chargemode"] = "time_load"
            if self.charge_template.data["chargemode"]["selected"] == "instant_load":
                self.data["set"]["required_current"] = self.charge_template.instant_load(self.data["get"]["soc"], self.data["get"]["charged_since_plugged_kwh"])
                self.data["set"]["chargemode"] = "instant_load"
            elif self.charge_template.data["chargemode"]["selected"] == "pv_load":
                self.data["set"]["required_current"], self.data["set"]["chargemode"] = self.charge_template.pv_load(self.data["get"]["soc"])
            # elif data.ev_charge_template_data[self.charge_template].chargemode == "scheduled_load":
            #     self.__scheduled_load()

            # self.__check_min_current()
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_required_current")
    

    def get_soc(self):
        """ermittelt den SoC, wenn die Zugangsdaten konfiguriert sind.
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
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in time_load")

    def instant_load(self, soc, amount):
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.

        Parameter
        ---------
        soc: int
            SoC des EV

        amount: int
            geladende Energiemenge seit das EV angesteckt wurde
        """
        try:
            instant_load = self.data["chargemode"]["instant_load"]
            if instant_load["selected"] == "none":
                return instant_load["current"]
            elif instant_load["selected"] == "soc":
                if soc < instant_load["limit"]["soc"]:
                    return instant_load["current"]
                else:
                    return 0
            elif instant_load["selected"] == "amount":
                if amount < instant_load["limit"]["amount"]:
                    return instant_load["current"]
                else:
                    return 0
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in instant_load")

    def pv_load(self, soc):
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.
        """
        try:
            pv_load= self.data["chargemode"]["pv_load"]
            if soc < pv_load["max_soc"]:
                if pv_load["min_soc"] != 0:
                    if soc < pv_load["min_soc"]:
                        return pv_load["min_soc_current"], "min_pv_load"
                    else:
                        return pv_load["min_current"], "pv_load"
                else:
                    return pv_load["min_current"], "pv_load"
            else:
                return 0, "pv_load"
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in pv_load")

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
            except KeyError as key:
                print("dictionary key", key, "related to loop-object", vehicle, "doesn't exist in get_ev_to_rfid")
    else:
        return None
    
