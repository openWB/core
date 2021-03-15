"""Zähler-Logik
"""

import data
import log

class counter():
    """
    """

    def __init__(self):
        self.data={}
        self.data["set"] = {}

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            if self.data["get"]["power_all"] > 0: #Import
                # <absicherung - Hausverbrauch
                self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"] - (self.data["get"]["power_all"] - data.cp_data["all"].data["get"]["power_all"])
                #self.data["set"]["current_left"] = [m - n for m,n in zip(self.data["config"]["max_current"], self.data["get"]["current"])]
            else: # Export
                self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"]
                #self.data["set"]["current_left"] = self.data["config"]["max_current"]
        except Exception as e:
            log.exception_logging(e)

class counterModule():
    """
    """

    def __init__(self):
        self.data={}
