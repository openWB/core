"""Zähler-Logik
"""

import subprocess

import data
import log
import pub

class counterHw():
    """
    """

    def __init__(self):
        self.hw_data={}
        self.counter_num = 0

    def get_counter_values(self):
        """ ermittelt die Zählermesswerte und ruft dazu das vorhandene Shell-Skript auf. Anschließend werden die Werte auf dem Broker gepublished.
        """
        if self.hw_data["config"]["module"]["selected"] == "http":
            http_config = self.hw_data["config"]["module"]["http"]
            output = subprocess.run(["./modules/bezug_http/main.sh",http_config["url_power"],http_config["url_imported"], http_config["url_exported"], http_config["url_current1"], http_config["url_current2"], http_config["url_current3"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if output.stderr.decode('utf-8') == "":
                # In UTF-8 dekodieren und in Liste ablegen.
                values = output.stdout.decode('utf-8').strip('\n').split('  ')
                # Werte publishen
                pub.pub("openWB/set/counter/"+self.counter_num+"/get/power_all", values[0])
                pub.pub("openWB/set/counter/"+self.counter_num+"/get/imported", values[1])
                pub.pub("openWB/set/counter/"+self.counter_num+"/get/exported", values[2])
                pub.pub("openWB/set/counter/"+self.counter_num+"/get/current", [values[3], values[4], values[5]])
            else:
                log.message_debug_log("error", "Beim Ausführen des Shell-Skripts ist ein Fehler aufgetreten: "+str(output.stderr.decode('utf-8')))

class counter(counterHw):
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
            if self.hw_data["get"]["power_all"] > 0:
                self.data["set"]["consumption_left"] = self.hw_data["config"]["max_consumption"] - self.hw_data["get"]["power_all"]
                if self.data["set"]["consumption_left"] < 0:
                    self.data["set"]["loadmanagement"] = True
                    log.message_debug_log("warning", "Lastamanagement aktiv. maximaler Bezug um "+str(self.data["set"]["consumption_left"]*-1)+"W ueberschritten.")
                else:
                    self.data["set"]["loadmanagement"] = False
                    log.message_debug_log("debug", "Lastmanagement nicht aktiv. "+str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")
            else:
                self.data["set"]["consumption_left"] = self.hw_data["config"]["max_consumption"]
                self.data["set"]["loadmanagement"] = False
                log.message_debug_log("debug", "Lastmanagement nicht aktiv. "+str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")
        except Exception as e:
            log.exception_logging(e)

    def put_stats(self):
        pub.pub("openWB/counter/evu/set/consumption_left", self.data["set"]["consumption_left"])
        log.message_debug_log("debug", str(self.data["set"]["consumption_left"])+"W EVU-Leistung, die noch bezogen werden kann.")


