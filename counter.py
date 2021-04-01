"""Zähler-Logik
"""

import subprocess

import data
import log
import pub

class counter():
    """
    """

    def __init__(self):
        super().__init__()
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
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        pub.pub("openWB/counter/evu/set/consumption_left", self.data["set"]["consumption_left"])
        log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")


