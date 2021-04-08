"""Zähler-Logik
"""

import subprocess

import data
import log
import pub

class counterAll():
    """
    """

    def __init__(self):
        self.data={}
        self.data["set"] = {}
        self.data["set"]["loadmanagement"] = False
        pub.pub("openWB/set/counter/set/loadmanagement", False)

    def put_stats(self):
        pub.pub("openWB/set/counter/set/loadmanagement", self.data["set"]["loadmanagement"])

class counter():
    """
    """

    def __init__(self):
        self.data={}
        self.data["set"] = {}

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            # Import
            if self.data["get"]["power_all"] > 0:
                self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"] - self.data["get"]["power_all"]
                if self.data["set"]["consumption_left"] < 0:
                    self.data["set"]["loadmanagement"] = True
                    log.message_debug_log("warning", "Lastamanagement aktiv. maximaler Bezug um "+str(self.data["set"]["consumption_left"]*-1)+"W ueberschritten.")
                else:
                    self.data["set"]["loadmanagement"] = False
                    log.message_debug_log("debug", "Lastmanagement nicht aktiv. "+str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")
            else:
                self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"]
                self.data["set"]["loadmanagement"] = False
                log.message_debug_log("debug", "Lastmanagement nicht aktiv. "+str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")
            # Strom
            self.data["set"]["current_used"] = self.data["get"]["current"]
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        pub.pub("openWB/set/counter/0/set/consumption_left", self.data["set"]["consumption_left"])
        log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")


