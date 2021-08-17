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
        # Hilfsvariablen für die rekursiven Funktionen
        self.connected_counters = []
        self.connected_chargepoints = []

    def put_stats(self):
        try:
            pub.pub("openWB/set/counter/set/loadmanagement", self.data["set"]["loadmanagement"])
        except Exception as e:
            log.exception_logging(e)

    # Hierarchie analysieren

    def get_chargepionts_of_counter(self, counter):
        """ gibt eine Liste der Ladepunkte, die in den folgenden Zweigen des Zählers sind, zurück.

        Parameter
        ---------
        counter: str
            Zähler, dessen Lp ermittelt werden sollen.

        Return
        ------
        chargepoints: list
            Ladepunkte, die in den folgenden Zweigen des Zählers sind
        """
        self.connected_chargepoints.clear()
        try:
            if counter == "counter0":
                counter_object = self.data["get"]["hierarchy"][0]
            else:
                counter_object = self._look_for_object(self.data["get"]["hierarchy"][0], "counter", counter[7:])
            self._get_all_cp_connected_to_counter(counter_object)
            return self.connected_chargepoints
        except Exception as e:
            log.exception_logging(e)
            return None

    def _get_all_cp_connected_to_counter(self, child):
        """ Rekursive Funktion, die alle Ladepunkte ermittelt, die an den angegebenen Zähler angeschlossen sind.

        Parameter
        ---------
        child: object
            Zähler, dessen Ladepunkte ermittelt werden sollen
        """
        # Alle Objekte der Ebene durchgehen
        for child in child["children"]:
            try:
                if "cp" in child["id"]:
                    self.connected_chargepoints.append(child["id"])
                # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
                elif len(child["children"]) != 0:
                    self._get_all_cp_connected_to_counter(child)
            except Exception as e:
                log.exception_logging(e)

    def get_counters_to_check(self, chargepoint):
        """ ermittelt alle Zähler, die für das Lastmanagement des angegebenen Ladepunkts relevant sind.

        Parameter
        ---------
        chargepoint: class
            Ladepunkt

        Return
        ------
        counters: list
            Liste der gesuchten Zähler
        """
        try:
            self.connected_counters.clear()
            self._look_for_object(self.data["get"]["hierarchy"][0], "cp", chargepoint.cp_num)
            return self.connected_counters
        except Exception as e:
            log.exception_logging(e)
            return None

    def _look_for_object(self, child, object, num):
        """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle Zähler in diesem Pfad der Liste anhängt.

        Parameter
        ---------
        child: object
            Zweig, der als nächstes durchsucht werden soll
        object: str "cp"/"counter"
            soll nach einem Ladepunkt oder einem Zähler in der Liste gesucht werden.
        num: int
            Nummer des gesuchten Ladepunkts/Zählers

        Return
        ------
        True/False: Ladepunkt wurde gefunden.
        """
        try:
            parent = child["id"]
            for child in child["children"]:
                try:
                    if object == "cp":
                        if "cp" in child["id"]:
                            if child["id"][2:] == str(num):
                                self.connected_counters.append(parent)
                                return True
                            else:
                                continue
                    elif object == "counter":
                        if "counter" in child["id"]:
                            if child["id"][7:] == str(num):
                                return child
                    else:
                        if len(child["children"]) != 0:
                            found = self._look_for_object(child, object, num)
                            if found != False:
                                if object == "cp":
                                    self.connected_counters.append(parent)
                                    return True
                            elif object == "counter":
                                return found
                except Exception as e:
                    log.exception_logging(e)
            else:
                return False
        except Exception as e:
            log.exception_logging(e)
            return False

class counter():
    """
    """

    def __init__(self, default):
        try:
            self.data={}
            if default == False:
                self.data["set"] = {}
                self.counter_num = None
        except Exception as e:
            log.exception_logging(e)

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


