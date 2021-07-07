"""Zähler-Logik
"""

from ..helpermodules import log
from ..helpermodules import pub

class counterAll():
    """
    """

    def __init__(self):
        self.data={}
        self.data["set"] = {}
        self.data["set"]["loadmanagement"] = False

    def put_stats(self):
        try:
            pub.pub("openWB/set/counter/set/loadmanagement", self.data["set"]["loadmanagement"])
        except Exception as e:
            log.exception_logging(e)

class counter():
    """
    """

    def __init__(self):
        self.data={}
        self.data["set"] = {}
        self.counter_num = None

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            # Nur beim EVU-Zähler (counter0) wird auch die maximale Leistung geprüft.
            if self.counter_num == "0":
                # max Leistung
                if self.data["get"]["power_all"] > 0:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"] - self.data["get"]["power_all"]
                else:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"]
                log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")
            # Strom
            self.data["set"]["current_used"] = self.data["get"]["current"]
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        try:
            pub.pub("openWB/set/counter/0/set/consumption_left", self.data["set"]["consumption_left"])
            log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception as e:
            log.exception_logging(e)

    def print_stats(self):
        try:
            log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception as e:
            log.exception_logging(e)


