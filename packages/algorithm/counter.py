"""Zähler-Logik
"""
from . import data
from ..helpermodules import log
from ..helpermodules.pub import Pub


class counterAll:
    """
    """

    def __init__(self):
        self.data = {"set": {"loadmanagement_active": False,
                             "loadmanagement_available": True,
                             "home_consumption": 0,
                             "invalid_home_consumption": 0,
                             "daily_yield_home_consumption": 0}}
        # Hilfsvariablen für die rekursiven Funktionen
        self.connected_counters = []
        self.connected_chargepoints = []

    def get_evu_counter(self):
        try:
            return self.data["get"]["hierarchy"][0]["id"]
        except Exception:
            log.MainLogger().error("Ohne Konfiguration eines EVU-Zählers ist keine Regelung möglich.")
            raise

    def put_stats(self):
        try:
            Pub().pub("openWB/set/counter/set/loadmanagement_active", self.data["set"]["loadmanagement_active"])
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")

    def calc_home_consumption(self):
        """ berechnet den Hausverbrauch.
        """
        try:
            evu = data.data.counter_data[self.get_evu_counter()].data["get"]["power_all"]
            pv = data.data.pv_data["all"].data["get"]["power"]
            bat = data.data.bat_data["all"].data["get"]["power"]
            cp = data.data.cp_data["all"].data["get"]["power_all"]
            home_consumption = int(evu - pv - bat - cp)
            if home_consumption < 0:
                if self.data["set"]["invalid_home_consumption"] < 3:
                    self.data["set"]["invalid_home_consumption"] += 1
                    return
                else:
                    self.data["set"]["invalid_home_consumption"] += 1
                    home_consumption = 0
            else:
                self.data["set"]["invalid_home_consumption"] = 0
                self.data["set"]["home_consumption"] = home_consumption
            Pub().pub("openWB/set/counter/set/invalid_home_consumption",  self.data["set"]["invalid_home_consumption"])
            Pub().pub("openWB/set/counter/set/home_consumption", self.data["set"]["home_consumption"])

        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")

    def calc_daily_yield_home_consumption(self):
        """ berechnet die heute im Haus verbrauchte Energie.
        """
        try:
            evu_imported = data.data.counter_data[self.get_evu_counter()].data["get"]["daily_yield_import"]
            evu_exported = data.data.counter_data[self.get_evu_counter()].data["get"]["daily_yield_export"]
            if len(data.data.pv_data) > 1:
                pv = data.data.pv_data["all"].data["get"]["daily_yield"]
            else:
                pv = 0
            if len(data.data.bat_data) > 1:
                bat_imported = data.data.bat_data["all"].data["get"]["daily_yield_import"]
                bat_exported = data.data.bat_data["all"].data["get"]["daily_yield_export"]
            else:
                bat_imported = 0
                bat_exported = 0
            if len(data.data.cp_data) > 1:
                cp = data.data.cp_data["all"].data["get"]["daily_yield"]
            else:
                cp = 0
            daily_yield_home_consumption = evu_imported + pv - cp + bat_exported - bat_imported - evu_exported
            Pub().pub("openWB/set/counter/set/daily_yield_home_consumption", daily_yield_home_consumption)
            self.data["set"]["daily_yield_home_consumption"] = daily_yield_home_consumption
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")

    # Hierarchie analysieren

    def get_chargepoints_of_counter(self, counter):
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
            if counter == self.get_evu_counter():
                counter_object = self.data["get"]["hierarchy"][0]
            else:
                counter_object = self._look_for_object(self.data["get"]["hierarchy"][0], "counter", counter[7:])
            self._get_all_cp_connected_to_counter(counter_object)
            return self.connected_chargepoints
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
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
            except Exception:
                log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")

    def get_counters_to_check(self, chargepoint):
        """ ermittelt alle Zähler im Zweig des Ladepunkts.

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
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
            return None

    def _look_for_object(self, child, object, num):
        """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle
        Zähler in diesem Pfad der Liste anhängt.

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
                    elif object == "counter":
                        if "counter" in child["id"]:
                            if child["id"][7:] == str(num):
                                return child
                    if len(child["children"]) != 0:
                        found = self._look_for_object(child, object, num)
                        if found:
                            if object == "cp":
                                self.connected_counters.append(parent)
                                return True
                        elif object == "counter":
                            return found
                except Exception:
                    log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse für "+child)
            else:
                return False
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
            return False

    def hierarchy_add_item_aside(self, id, lower_level):
        """ ruft die rekursive Funktion zum Hinzufügen eines Zählers oder Ladepunkts in die Zählerhierarchie auf
        derselben Ebene wie das angegebene Element.

        Parameter
        ---------
        id: str (counterX/cpX)
            Id des neuen Elements
        lower_level: str
            Id des Elements, auf dessen Ebene das neue Element eingefügt werden soll.
        """
        return self._add_item_aside(self.data["get"]["hierarchy"][0], id, lower_level)

    def _add_item_aside(self, upper_level, id, lower_level):
        try:
            for child in upper_level["children"]:
                try:
                    if lower_level in child["id"]:
                        upper_level["children"].append({"id": id, "children": []})
                        Pub().pub(
                            "openWB/set/counter/get/hierarchy",
                            data.data.counter_data["all"].data["get"]["hierarchy"])
                        return True
                    else:
                        if len(child["children"]) != 0:
                            added = self._add_item_aside(child, id, lower_level)
                            return added
                except Exception:
                    log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse für "+child)
            else:
                return False
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
            return False

    def hierarchy_remove_item(self, id, keep_children=True):
        """ruft die rekursive Funtion zum Löschen eines Elements. Je nach Flag werden die Kinder gelöscht oder auf die
        Ebene des gelöschten Elements gehoben.

        Parameter
        ---------
        id: str (counterX/cpX)
            Id des zu löschenden Elements
        """
        return self._remove_item(self.data["get"]["hierarchy"][0], id, keep_children)

    def _remove_item(self, upper_level, id, keep_children):
        try:
            for child in upper_level["children"]:
                try:
                    if id in child["id"]:
                        if keep_children:
                            upper_level["children"].extend(child["children"])
                        upper_level["children"].remove(child)
                        Pub().pub(
                            "openWB/set/counter/get/hierarchy",
                            data.data.counter_data["all"].data["get"]["hierarchy"])
                        return True
                    else:
                        if len(child["children"]) != 0:
                            removed = self._remove_item(child, id, keep_children)
                            return removed
                except Exception:
                    log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse für "+child)
            else:
                return False
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
            return False

    def hierarchy_add_item_below(self, id, below):
        """ruft die rekursive Funktion zum Hinzufügen eines Elements als Kind des angegebenen Elements.

        Parameter
        ---------
        id: str (counterX/cpX)
            Id des neuen Elements
        lower_level: str
            Id des Elements, als dessen Kind das neue Element eingefügt werden soll.
        """
        try:
            if below in self.data["get"]["hierarchy"][0]["id"]:
                self.data["get"]["hierarchy"][0]["children"].append({"id": id, "children": []})
                Pub().pub("openWB/set/counter/get/hierarchy", data.data.counter_data["all"].data["get"]["hierarchy"])
                return True
            else:
                if len(self.data["get"]["hierarchy"][0]["children"]) != 0:
                    added = self._add_item_below(self.data["get"]["hierarchy"][0], id, below)
                    return added
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
            return False

    def _add_item_below(self, upper_level, id, below):
        try:
            for child in upper_level["children"]:
                try:
                    if below in child["id"]:
                        child["children"].append({"id": id, "children": []})
                        Pub().pub("openWB/set/counter/get/hierarchy",
                                  data.data.counter_data["all"].data["get"]["hierarchy"])
                        return True
                    else:
                        if len(child["children"]) != 0:
                            added = self._add_item_below(child, id, below)
                            return added
                except Exception:
                    log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse für "+child)
            else:
                return False
        except Exception:
            log.MainLogger().exception("Fehler in der allgemeinen Zaehler-Klasse")
            return False


class counter:
    """
    """

    def __init__(self, index):
        try:
            self.data = {"set": {},
                         "get": {
                "daily_yield_export": 0,
                "daily_yield_import": 0}}
            self.counter_num = index
        except Exception:
            log.MainLogger().exception("Fehler in der Zaehler-Klasse von "+str(self.counter_num))

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            # Nur beim EVU-Zähler (counter0) wird auch die maximale Leistung geprüft.
            if self.counter_num == 0:
                # Wenn der EVU-Zähler keine Werte liefert, darf nicht geladen werden.
                if self.data["get"]["fault_state"] > 0:
                    data.data.counter_data["all"].data["set"]["loadmanagement_available"] = False
                    self.data["get"]["power_all"] = 0
                    return
                else:
                    data.data.counter_data["all"].data["set"]["loadmanagement_available"] = True
                # max Leistung
                if self.data["get"]["power_all"] > 0:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"]
                    - self.data["get"]["power_all"]
                else:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_consumption"]
                log.MainLogger().debug(str(self.data["set"]["consumption_left"]) +
                                       "W EVU-Leistung, die noch bezogen werden kann.")
            # Strom
            self.data["set"]["current_used"] = self.data["get"]["current"]
        except Exception:
            log.MainLogger().exception("Fehler in der Zaehler-Klasse von "+str(self.counter_num))

    def put_stats(self):
        try:
            Pub().pub("openWB/set/counter/0/set/consumption_left", self.data["set"]["consumption_left"])
            log.MainLogger().debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            log.MainLogger().exception("Fehler in der Zaehler-Klasse von "+str(self.counter_num))

    def print_stats(self):
        try:
            log.MainLogger().debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            log.MainLogger().exception("Fehler in der Zaehler-Klasse von "+str(self.counter_num))
