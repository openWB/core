""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.
"""

import data
import general
import optional
import timecheck

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
            elif self.charge_template.data["chargemode"]["selected"] == "scheduled_load":
                self.data["set"]["required_current"], self.data["set"]["chargemode"] = self.charge_template.scheduled_load(self.data["get"]["soc"], self.ev_template.data["max_current"], self.ev_template.data["battery_capacity"], self.ev_template.data["max_phases"])
            self.__check_min_current()
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in get_required_current")
    

    def get_soc(self):
        """ermittelt den SoC, wenn die Zugangsdaten konfiguriert sind.
        """
        pass

    def __check_min_current(self):
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom des EVs liegt. Falls nicht, wird der 
        Ladestrom auf den Mindest-Ladestrom des EV gesetzt.
        """
        try:
            if self.data["set"]["required_current"] < self.ev_template.data["min_current"]:
                self.data["set"]["required_current"] = self.ev_template.data["min_current"]
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in __check_min_current")

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
                plan = timecheck.check_plans_timeframe(self.data["time_load"])
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

        Parameter
        ---------
        soc: int
            SoC des EV

        Return
        ------
        Required Current, Chargemode: int, str
            Therotisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        try:
            pv_load= self.data["chargemode"]["pv_load"]
            if soc < pv_load["max_soc"]:
                if pv_load["min_soc"] != 0:
                    if soc < pv_load["min_soc"]:
                        return pv_load["min_soc_current"], "instant_load"
                    else:
                        return pv_load["min_current"], "pv_load"
                else:
                    if pv_load["min_current"] == 0:
                        return 0, "pv_load" #nur PV
                    else:
                        return pv_load["min_current"], "pv_load" #Min PV
            else:
                return 0, "stop" 
        except KeyError as key:
            print("dictionary key", key, "doesn't exist in pv_load")

    def scheduled_load(self, soc, max_current, battery_capacity, max_phases):
        """ prüft, ob der Ziel-SoC erreicht wurde und stellt den zur Erreichung nötigen Ladestrom ein.

        Parameter
        ---------
            soc: int
                Akkustand

            max_current: int
                maximaler Ladestrom

            battery_capacity: float
                Akkugröße

            max_phases: int
                maximale Anzahl Phasen, mit denen das EV laden kann.

        Return
        ------
            Required Current, Chargemode: int, str
                Therotisch benötigter Strom, Ladmodus(soll geladen werden, auch wenn kein PV-Strom zur Verfügung steht)
        """
        for plan in self.data["chargemode"]["scheduled_load"]:
            if self.data["chargemode"]["scheduled_load"][plan]["active"] == True:
                try:
                    if soc < self.data["chargemode"]["scheduled_load"][plan]["soc"]:
                        phases_scheduled_load = data.general_data["general"].get_phases_chargemode("scheduled_load")
                        if max_phases <= phases_scheduled_load:
                            usable_phases = max_phases
                        else:
                            usable_phases = phases_scheduled_load

                        available_current = 0.8*max_current*usable_phases
                        required_wh = ((self.data["chargemode"]["scheduled_load"][plan]["soc"] - soc)/100) *battery_capacity*1000
                        duration = required_wh/(available_current*230)
                        start, remaining_time = timecheck.check_duration(self.data["chargemode"]["scheduled_load"][plan], duration)
                        if start == 1:
                            return available_current, "instant_load"
                        elif start == 2: # weniger als die berechnete Zeit verfügbar
                            required_current = required_wh/(remaining_time*230)
                            if required_current <= max_current:
                                return required_current, "instant_load"
                            else:
                                return max_current, "instant_load"
                        else:
                            if timecheck.check_timeframe(self.data["chargemode"]["scheduled_load"][plan], 24) == True:
                                if data.optional_data["optional"].data["et"]["active"] == True:
                                    hourlist = data.optional_data["optional"].get_loading_hours(duration)
                                    if timecheck.is_list_valid(hourlist) == True:
                                        return available_current, "instant_load"
                                    else:
                                        return 0, "pv_load"
                                else:
                                    return 0, "pv_load"
                            else:
                                return 0, "scheduled_load"
                    else:
                        return 0, "stop"
                except KeyError as key:
                    print("dictionary key", key, "related to loop-object", plan, "doesn't exist in scheduled_load")
        else:
            #log
            print("Keine aktiven Zeit-Pläne.")
            return 0, "scheduled_load"