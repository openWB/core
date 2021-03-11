"""Hausspeicher-Logik
"""

import inspect

import data
import log
import pub

class bat:
    def __init__(self):
        self.data={}
        self.charging_power_left = 0

    def setup_bat(self):
        if "get" not in self.data:
            self.data["get"]={}
        if "config" not in self.data:
            self.data["config"]={}
        if len(data.bat_module_data) > 1:
            self.data["config"]["configured"] = True
            for module in data.bat_module_data:
                if "bat" in module:
                    try:
                        if data.bat_module_data[module].data["get"]["power"] > 0:
                            self.charging_power_left += data.bat_module_data[module].data["get"]["power"]
                    except Exception as e:
                        log.exception_logging(e)
        else:
            self.data["config"]["configured"] = False
            self.charging_power_left = 0

    def power_for_bat_charging(self):
        if self.data["config"]["configured"] == True:
            return self.charging_power_left
        else:
            return 0

    def allocate_bat_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung von der verfügbaren Speicher-Leistung

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll
        """
        if self.data["config"]["configured"] == True:
            self.charging_power_left -= required_power
            if self.charging_power_left < 0:
                pass #error

    def put_stats(self):
        """ Publishen und Loggen der verbleibnden PV-Leistung und reservierten Leistung
        """
        pub.pub("openWB/bat/config/configured", self.data["config"]["configured"])
        if self.data["config"]["configured"] == True:
            pub.pub("openWB/bat/get/charging_power_left", self.charging_power_left)
            log.message_debug_log("debug", "Fuer die folgenden Algorithmus-Durchlaeufe verbleibende Speicher-Leistung "+str(self.charging_power_left)+"W")

class batModule():
    """
    """

    def __init__(self):
        self.data={}