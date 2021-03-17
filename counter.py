"""Zähler-Logik
"""

import data
import log
import pub

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
            else:
                self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"]
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        pub.pub("openWB/counter/evu/set/consumption_left", self.data["set"]["consumption_left"])
        log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")


class counterModule():
    """
    """

    def __init__(self):
        self.data={}
