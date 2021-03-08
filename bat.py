"""Hausspeicher-Logik
"""

import inspect

import data
import log

class bat:
    def __init__(self):
        self.data={}

    def setup_bat(self):
        self.data["set"]={}
        if len(data.bat_module_data) > 1:
            for module in data.bat_module_data:
                if "bat" in module:
                    try:
                        if data.bat_module_data[module].data["get"]["power"] > 0:
                            self.data["set"]["charging_power_left"] += data.bat_module_data[module].data["get"]["power"]
                    except KeyError as key:
                        log.log_key_error(str(key))
        else:
            self.data["set"]["charging_power_left"] = 0

class batModule():
    """
    """

    def __init__(self):
        self.data={}