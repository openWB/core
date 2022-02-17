"""Zähler-Logik
"""
from typing import Callable, Dict, List
from control import data
from helpermodules.log import MainLogger
from helpermodules.pub import Pub
from modules.common.component_type import ComponentType


class CounterAll:
    """
    """

    def __init__(self):
        self.data = {"set": {"loadmanagement_active": False,
                             "home_consumption": 0,
                             "invalid_home_consumption": 0,
                             "daily_yield_home_consumption": 0}}
        # Hilfsvariablen für die rekursiven Funktionen
        self.connected_counters = []
        self.connected_chargepoints = []

    def get_evu_counter(self) -> str:
        return f"counter{self.get_id_evu_counter()}"

    def get_id_evu_counter(self) -> int:
        try:
            for item in self.data["get"]["hierarchy"]:
                if ComponentType.COUNTER.value == item["type"]:
                    return item['id']
            else:
                raise TypeError
        except Exception:
            MainLogger().error(
                "Ohne Konfiguration eines EVU-Zählers an der Spitze der Hierarchie ist keine Regelung möglich.")
            raise

    def put_stats(self):
        try:
            Pub().pub("openWB/set/counter/set/loadmanagement_active", self.data["set"]["loadmanagement_active"])
        except Exception:
            MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")

    def calc_home_consumption(self):
        """ berechnet den Hausverbrauch.
        """
        try:
            evu = data.data.counter_data[self.get_evu_counter()].data["get"]["power"]
            pv = data.data.pv_data["all"].data["get"]["power"]
            bat = data.data.bat_data["all"].data["get"]["power"]
            cp = data.data.cp_data["all"].data["get"]["power"]
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
            MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")

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
            MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")

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
                counter_object = self._look_for_object(
                    self.data["get"]["hierarchy"][0],
                    ComponentType.COUNTER, int(counter[7:]))
            self._get_all_cp_connected_to_counter(counter_object)
            return self.connected_chargepoints
        except Exception:
            MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")
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
                if child["type"] == ComponentType.CHARGEPOINT.value:
                    self.connected_chargepoints.append(f"cp{child['id']}")
                # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
                elif len(child["children"]) != 0:
                    self._get_all_cp_connected_to_counter(child)
            except Exception:
                MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")

    def get_counters_to_check(self, cp_num: int):
        """ ermittelt alle Zähler im Zweig des Ladepunkts.

        Return
        ------
        counters: list
            Liste der gesuchten Zähler
        """
        try:
            self.connected_counters.clear()
            self._look_for_object(self.data["get"]["hierarchy"][0], ComponentType.CHARGEPOINT, cp_num)
            return self.connected_counters
        except Exception:
            MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")
            return None

    def _look_for_object(self, child: Dict, object: ComponentType, id_to_find: int):
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
            parent_id = child["id"]
            for child in child["children"]:
                try:
                    if object == ComponentType.CHARGEPOINT:
                        if child["type"] == ComponentType.CHARGEPOINT.value:
                            if child["id"] == id_to_find:
                                self.connected_counters.append(f"counter{parent_id}")
                                return True
                    elif object == ComponentType.COUNTER:
                        if child["type"] == ComponentType.COUNTER.value:
                            if child["id"] == id_to_find:
                                return child
                    if len(child["children"]) != 0:
                        found = self._look_for_object(child, object, id_to_find)
                        if found:
                            if object == ComponentType.CHARGEPOINT:
                                self.connected_counters.append(f"counter{parent_id}")
                                return True
                        elif object == ComponentType.COUNTER:
                            return found
                except Exception:
                    MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse für "+str(child))
            else:
                return False
        except Exception:
            MainLogger().exception("Fehler in der allgemeinen Zähler-Klasse")
            return False

    def hierarchy_add_item_aside(self, new_id: int, new_type: ComponentType, id_to_find: int) -> bool:
        """ ruft die rekursive Funktion zum Hinzufügen eines Zählers oder Ladepunkts in die Zählerhierarchie auf
        derselben Ebene wie das angegebene Element.
        """
        if id_to_find == self.data["get"]["hierarchy"][0]["id"]:
            self.data["get"]["hierarchy"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return self.__find_element_in_hierarchy(
                self.data["get"]["hierarchy"][0],
                id_to_find, self._add_item_aside, new_id, new_type)

    def _add_item_aside(
            self, child: Dict, current_entry: Dict, id_to_find: int, new_id: int, new_type: ComponentType) -> bool:
        if id_to_find == child["id"]:
            current_entry["children"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return False

    def hierarchy_remove_item(self, id_to_find: int, keep_children: bool = True) -> bool:
        """ruft die rekursive Funktion zum Löschen eines Elements. Je nach Flag werden die Kinder gelöscht oder auf die
        Ebene des gelöschten Elements gehoben.
        """
        if self.data["get"]["hierarchy"][0]["id"] == id_to_find:
            if keep_children:
                self.data["get"]["hierarchy"].extend(self.data["get"]["hierarchy"][0]["children"])
            self.data["get"]["hierarchy"].remove(self.data["get"]["hierarchy"][0])
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return self.__find_element_in_hierarchy(
                self.data["get"]["hierarchy"][0],
                id_to_find, self._remove_item, keep_children)

    def _remove_item(self, child: Dict, current_entry: Dict, id: str, keep_children: bool) -> bool:
        if id == child["id"]:
            if keep_children:
                current_entry["children"].extend(child["children"])
            current_entry["children"].remove(child)
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return False

    def hierarchy_add_item_below(self, new_id: int, new_type: ComponentType, id_to_find: int):
        """ruft die rekursive Funktion zum Hinzufügen eines Elements als Kind des angegebenen Elements.
        """
        if id_to_find == self.data["get"]["hierarchy"][0]["id"]:
            self.data["get"]["hierarchy"][0]["children"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return self.__find_element_in_hierarchy(
                self.data["get"]["hierarchy"][0],
                id_to_find, self._add_item_below, new_id, new_type)

    def _add_item_below(self, child: Dict, current_entry: Dict, id_to_find: int, new_id: int, new_type: ComponentType):
        if id_to_find == child["id"]:
            child["children"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return False

    def __find_element_in_hierarchy(self, current_entry: Dict, id_to_find: int, func: Callable, *args) -> bool:
        for child in current_entry["children"]:
            if func(child, current_entry, id_to_find, *args):
                return True
            else:
                if len(child["children"]) != 0:
                    return self.__find_element_in_hierarchy(child, id_to_find, func, *args)
        else:
            raise ValueError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")


def get_max_id_in_hierarchy(current_entry: List, max_id: int) -> int:
    for item in current_entry:
        if item["id"] > max_id:
            max_id = item["id"]
        if len(item["children"]) != 0:
            max_id = get_max_id_in_hierarchy(item["children"], max_id)
    else:
        return max_id


def get_counter_default_config():
    return {"max_currents": [16, 16, 16],
            "max_total_power": 11000}


class Counter:
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
            MainLogger().exception("Fehler in der Zähler-Klasse von "+str(self.counter_num))

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            # Wenn der Zähler keine Werte liefert, darf nicht geladen werden.
            connected_cps = data.data.counter_data["all"].get_chargepoints_of_counter(f'counter{self.counter_num}')
            for cp in connected_cps:
                if self.data["get"]["fault_state"] > 0:
                    data.data.cp_data[cp].data["set"]["loadmanagement_available"] = False
                else:
                    data.data.cp_data[cp].data["set"]["loadmanagement_available"] = True
            if self.data["get"]["fault_state"] > 0:
                self.data["get"]["power"] = 0
                return

            # Nur beim EVU-Zähler wird auch die maximale Leistung geprüft.
            if f'counter{self.counter_num}' == data.data.counter_data["all"].get_evu_counter():
                # max Leistung
                if self.data["get"]["power"] > 0:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_total_power"] \
                        - self.data["get"]["power"]
                else:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_total_power"]
                MainLogger().debug(str(self.data["set"]["consumption_left"]) +
                                   "W EVU-Leistung, die noch bezogen werden kann.")
            # Strom
            try:
                self.data["set"]["currents_used"] = self.data["get"]["currents"]
            except KeyError:
                MainLogger().warning(f"Zähler {self.counter_num}: Einzelwerte für Zähler-Phasenströme unbekannt")
                self.data["set"]["state_str"] = "Das Lastmanagement regelt nur anhand der Gesamtleistung, da keine \
                    Phasenströme ermittelt werden konnten."
                Pub().pub("openWB/set/counter/"+str(self.counter_num) + "/set/state_str",
                          self.data["set"]["state_str"])
        except Exception:
            MainLogger().exception("Fehler in der Zähler-Klasse von "+str(self.counter_num))

    def put_stats(self):
        try:
            if f'counter{self.counter_num}' == data.data.counter_data["all"].get_evu_counter():
                Pub().pub("openWB/set/counter/"+str(self.counter_num)+"/set/consumption_left",
                          self.data["set"]["consumption_left"])
                MainLogger().debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            MainLogger().exception("Fehler in der Zähler-Klasse von "+str(self.counter_num))

    def print_stats(self):
        try:
            MainLogger().debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            MainLogger().exception("Fehler in der Zähler-Klasse von "+str(self.counter_num))
