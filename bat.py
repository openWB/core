"""Hausspeicher-Logik
Der Hausspeicher ist immer bestrebt, den EVU-Überschuss auf 0 zu regeln.
Wenn EVU_Überschuss vorhanden ist, lädt der Speicher. Wenn EVU-Bezug vorhanden wäre, 
entlädt der Speicher, sodass kein Netzbezug stattfindet. Wenn das EV Vorrang hat, wird 
eine Ladung gestartet und der Speicher hört automatisch auf zu laden, da sonst durch 
das Laden des EV Bezug statt finden würde.
"""

import subprocess

import data
import log
import pub

class bat:
    def __init__(self):
        self.data={}
        pub.pub("openWB/bat/config/configured", False)
        pub.pub("openWB/pv/set/charging_power_left", 0)
        if "get" not in self.data:
            self.data["get"]={}
        if "set" not in self.data:
            self.data["set"]={}
        if "config" not in self.data:
            self.data["config"]={}
        self.data["config"]["configured"] = False
        self.data["set"]["charging_power_left"] = 0
        self.data["set"]["switch_on_soc_reached"] = 0
        self.data["get"]["power"] = 0

    def setup_bat(self):
        try:
            if len(data.bat_module_data) > 1:
                if "all" not in data.bat_module_data:
                    data.bat_module_data["all"] = {}
                self.data["config"]["configured"] = True
                # Speicher lädt
                if self.data["get"]["power"] > 0:
                    # Laderegelung wurde noch nicht freigegeben
                    if self.data["set"]["switch_on_soc_reached"] == False:
                        if self.data["config"]["switch_on_soc"] != 0:
                            if self.data["config"]["switch_on_soc"] < self.data["get"]["soc"]:
                                self.data["set"]["switch_on_soc_reached"] == True
                                self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                            else:
                                self.data["set"]["charging_power_left"] = 0
                        else:
                            # Kein Einschalt-Soc; Nutzung, wenn Soc über Ausschalt-Soc liegt.
                            if self.data["config"]["switch_off_soc"] != 0:
                                if self.data["config"]["switch_off_soc"] < self.data["get"]["soc"]:
                                    self.data["set"]["switch_on_soc_reached"] == True
                                    self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                                else:
                                    self.data["set"]["switch_on_soc_reached"] == False
                                    self.data["set"]["charging_power_left"] = 0
                            # Weder Einschalt- noch Ausschalt-Soc sind konfiguriert.
                            else:
                                self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                    # Laderegelung wurde freigegeben.
                    elif self.data["set"]["switch_on_soc_reached"] == True:
                        if self.data["config"]["switch_off_soc"] != 0:
                            # Greift der Ausschalt-Soc?
                            if self.data["config"]["switch_off_soc"] < self.data["get"]["soc"]:
                                self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                            else:
                                self.data["set"]["switch_on_soc_reached"] == False
                                self.data["set"]["charging_power_left"] = 0
                        # Wenn kein Ausschalt-Soc konfiguriert wurde, wird der Speicher komplett entladen.
                        else:
                            if 0 < self.data["get"]["soc"]:
                                self.data["set"]["charging_power_left"] = self.data["get"]["power"]
                            else:
                                self.data["set"]["switch_on_soc_reached"] == False
                                self.data["set"]["charging_power_left"] = 0
                # Speicher wird entladen -> Wert wird ebenfalls benötigt, um zu prüfen, ob Abschaltschwelle erreicht wird.
                else:
                    self.data["set"]["charging_power_left"] = self.data["get"]["power"]
            else:
                self.data["config"]["configured"] = False
                self.data["set"]["charging_power_left"] = 0
                self.data["get"]["power"] = 0
            pub.pub("openWB/bat/config/configured", self.data["config"]["configured"])
            pub.pub("openWB/pv/set/charging_power_left", self.data["set"]["charging_power_left"])
        except Exception as e:
            log.exception_logging(e)

    def get_power(self):
        try:
            if self.data["config"]["configured"] == True:
                return self.data["get"]["power"]
            else:
                return 0
        except Exception as e:
            log.exception_logging(e)

    def power_for_bat_charging(self):
        try:
            if self.data["config"]["configured"] == True:
                return self.data["set"]["charging_power_left"]
            else:
                return 0
        except Exception as e:
            log.exception_logging(e)

    def allocate_bat_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung von der verfügbaren Speicher-Leistung

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll

        Return
        ------
        True: Leistung konnte allokiert werden.
        False: Leistung konnte nicht allokiert werden.
        """
        try:
            if self.data["config"]["configured"] == True:
                self.data["set"]["charging_power_left"] -= required_power
                if self.data["set"]["charging_power_left"] < 0:
                    self.data["set"]["charging_power_left"] += required_power
                    log.message_debug_log("error", "Es wurde versucht, mehr Speicher-Leistung zu allokieren, als geladen wird.")
                    return False
            return True
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        """ Publishen und Loggen der verbleibnden PV-Leistung und reservierten Leistung
        """
        try:
            pub.pub("openWB/bat/config/configured", self.data["config"]["configured"])
            if self.data["config"]["configured"] == True:
                pub.pub("openWB/bat/set/charging_power_left", self.data["set"]["charging_power_left"])
                log.message_debug_log("debug", str(self.data["set"]["charging_power_left"])+"W Speicher-Leistung , die fuer die folgenden Ladepunkte uebrig ist.")
        except Exception as e:
            log.exception_logging(e)
