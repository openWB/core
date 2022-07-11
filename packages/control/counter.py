"""Zähler-Logik
"""
import logging
from typing import Callable, Dict, List

from control import data
from helpermodules.pub import Pub
from modules.common.component_type import ComponentType
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


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
            log.error(
                "Ohne Konfiguration eines EVU-Zählers an der Spitze der Hierarchie ist keine Regelung möglich.")
            raise

    def put_stats(self):
        try:
            Pub().pub("openWB/set/counter/set/loadmanagement_active", self.data["set"]["loadmanagement_active"])
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def calc_home_consumption(self) -> None:
        try:
            power = 0
            elements = self.get_entry_of_element(self.get_id_evu_counter())["children"]
            for element in elements:
                if element["type"] == ComponentType.CHARGEPOINT.value:
                    power += data.data.cp_data[f"cp{element['id']}"].data.get.power
                elif element["type"] == ComponentType.BAT.value:
                    power += data.data.bat_data[f"bat{element['id']}"].data["get"]["power"]
                elif element["type"] == ComponentType.COUNTER.value:
                    power += data.data.counter_data[f"counter{element['id']}"].data["get"]["power"]
                elif element["type"] == ComponentType.INVERTER.value:
                    power += data.data.pv_data[f"pv{element['id']}"].data["get"]["power"]
            evu_counter_data = data.data.counter_data[self.get_evu_counter()].data
            evu = evu_counter_data["get"]["power"]

            home_consumption = int(evu - power)
            if home_consumption < 0:
                log.error(
                    f"Ungültiger Hausverbrauch: Leistung der Elemente {power}W, "
                    f"EVU-Leistung {evu}W, Berücksichtigte Komponenten neben EVU {elements}")
                if evu_counter_data["get"]["fault_state"] == FaultStateLevel.NO_ERROR:
                    evu_counter_data["get"]["fault_state"] = FaultStateLevel.WARNING.value
                    evu_counter_data["get"][
                        "fault_str"] = "Der Wert für den Hausverbrauch ist nicht plausibel (negativ). Bitte "\
                        "die Leistungen der Komponenten und die Anordnung in der Hierarchie prüfen."
                    evu_counter = self.get_id_evu_counter()
                    Pub().pub(f"openWB/set/counter/{evu_counter}/get/fault_state",
                              evu_counter_data["get"]["fault_state"])
                    Pub().pub(f"openWB/set/counter/{evu_counter}/get/fault_str", evu_counter_data["get"]["fault_str"])
                if self.data["set"]["invalid_home_consumption"] < 3:
                    self.data["set"]["invalid_home_consumption"] += 1
                    Pub().pub("openWB/set/counter/set/invalid_home_consumption",
                              self.data["set"]["invalid_home_consumption"])
                    return
                else:
                    home_consumption = 0
            else:
                self.data["set"]["invalid_home_consumption"] = 0
                Pub().pub("openWB/set/counter/set/invalid_home_consumption",
                          self.data["set"]["invalid_home_consumption"])
            self.data["set"]["home_consumption"] = home_consumption
            Pub().pub("openWB/set/counter/set/home_consumption", self.data["set"]["home_consumption"])
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def calc_daily_yield_home_consumption(self):
        """ berechnet die heute im Haus verbrauchte Energie.
        """
        try:
            evu_imported = data.data.counter_data[self.get_evu_counter()].data["get"]["daily_imported"]
            evu_exported = data.data.counter_data[self.get_evu_counter()].data["get"]["daily_exported"]
            if len(data.data.pv_data) > 1:
                pv = data.data.pv_data["all"].data["get"]["daily_exported"]
            else:
                pv = 0
            if len(data.data.bat_data) > 1:
                bat_imported = data.data.bat_data["all"].data["get"]["daily_imported"]
                bat_exported = data.data.bat_data["all"].data["get"]["daily_exported"]
            else:
                bat_imported = 0
                bat_exported = 0
            if len(data.data.cp_data) > 1:
                cp_imported = data.data.cp_all_data.data.get.daily_imported
                cp_exported = data.data.cp_all_data.data.get.daily_exported
            else:
                cp_imported, cp_exported = 0, 0
            daily_yield_home_consumption = (evu_imported + pv - cp_imported + cp_exported + bat_exported
                                            - bat_imported - evu_exported)
            Pub().pub("openWB/set/counter/set/daily_yield_home_consumption", daily_yield_home_consumption)
            self.data["set"]["daily_yield_home_consumption"] = daily_yield_home_consumption
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")

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
                counter_object = self.__get_entry(
                    self.data["get"]["hierarchy"][0],
                    int(counter[7:]),
                    self.__get_entry_of_element)
            self._get_all_cp_connected_to_counter(counter_object)
            return self.connected_chargepoints
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")
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
                log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def get_counters_to_check(self, num: int):
        """ ermittelt alle Zähler im Zweig des Ladepunkts.

        Return
        ------
        counters: list
            Liste der gesuchten Zähler
        """
        try:
            self.connected_counters.clear()
            self.__get_all_counter_in_branch(self.data["get"]["hierarchy"][0], num)
            return self.connected_counters
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")
            return None

    def get_entry_of_element(self, id_to_find: int) -> Dict:
        item = self.__is_id_in_top_level(id_to_find)
        if item:
            return item
        else:
            return self.__get_entry(self.data["get"]["hierarchy"][0], id_to_find, self.__get_entry_of_element)

    def get_entry_of_parent(self, id_to_find: int) -> Dict:
        if self.__is_id_in_top_level(id_to_find):
            return {}
        for child in self.data["get"]["hierarchy"][0]["children"]:
            if child["id"] == id_to_find:
                return self.data["get"]["hierarchy"][0]
        else:
            return self.__get_entry(self.data["get"]["hierarchy"][0], id_to_find, self.__get_entry_of_parent)

    def __is_id_in_top_level(self, id_to_find: int) -> Dict:
        for item in self.data["get"]["hierarchy"]:
            if item["id"] == id_to_find:
                return item
        else:
            return {}

    def __get_all_counter_in_branch(self, child: Dict, id_to_find: int):
        """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle
        Zähler in diesem Pfad der Liste anhängt.

        Parameter
        ---------
        child: object
            Zweig, der als nächstes durchsucht werden soll
        num: int
            Nummer des gesuchten Ladepunkts/Zählers

        Return
        ------
        True/False: Ladepunkt wurde gefunden.
        """
        parent_id = child["id"]
        for child in child["children"]:
            if child["id"] == id_to_find:
                self.connected_counters.append(f"counter{parent_id}")
                return True
            if len(child["children"]) != 0:
                found = self.__get_all_counter_in_branch(child, id_to_find)
                if found:
                    self.connected_counters.append(f"counter{parent_id}")
                    return True
        else:
            return False

    def __get_entry(self, child: Dict, id_to_find: int, func: Callable[[Dict, int], bool]) -> Dict:
        for child in child["children"]:
            found = func(child, id_to_find)
            if found:
                return child
            if len(child["children"]) != 0:
                entry = self.__get_entry(child, id_to_find, func)
                if entry:
                    return entry
        else:
            return {}

    def __get_entry_of_element(self, child: Dict, id_to_find: int) -> bool:
        if child["id"] == id_to_find:
            return True
        else:
            return False

    def __get_entry_of_parent(self, child: Dict, id_to_find: int) -> bool:
        for child2 in child["children"]:
            if child2["id"] == id_to_find:
                return True
        else:
            return False

    def hierarchy_add_item_aside(self, new_id: int, new_type: ComponentType, id_to_find: int) -> None:
        """ ruft die rekursive Funktion zum Hinzufügen eines Zählers oder Ladepunkts in die Zählerhierarchie auf
        derselben Ebene wie das angegebene Element.
        """
        if self.__is_id_in_top_level(id_to_find):
            self.data["get"]["hierarchy"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
        else:
            if (self.__edit_element_in_hierarchy(
                    self.data["get"]["hierarchy"][0],
                    id_to_find, self._add_item_aside, new_id, new_type) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _add_item_aside(
            self, child: Dict, current_entry: Dict, id_to_find: int, new_id: int, new_type: ComponentType) -> bool:
        if id_to_find == child["id"]:
            current_entry["children"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return False

    def hierarchy_remove_item(self, id_to_find: int, keep_children: bool = True) -> None:
        """ruft die rekursive Funktion zum Löschen eines Elements. Je nach Flag werden die Kinder gelöscht oder auf die
        Ebene des gelöschten Elements gehoben.
        """
        item = self.__is_id_in_top_level(id_to_find)
        if item:
            if keep_children:
                self.data["get"]["hierarchy"].extend(item["children"])
            self.data["get"]["hierarchy"].remove(item)
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
        else:
            if (self.__edit_element_in_hierarchy(
                    self.data["get"]["hierarchy"][0],
                    id_to_find, self._remove_item, keep_children) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _remove_item(self, child: Dict, current_entry: Dict, id: str, keep_children: bool) -> bool:
        if id == child["id"]:
            if keep_children:
                current_entry["children"].extend(child["children"])
            current_entry["children"].remove(child)
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return False

    def hierarchy_add_item_below(self, new_id: int, new_type: ComponentType, id_to_find: int) -> None:
        """ruft die rekursive Funktion zum Hinzufügen eines Elements als Kind des angegebenen Elements.
        """
        item = self.__is_id_in_top_level(id_to_find)
        if item:
            item["children"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
        else:
            if (self.__edit_element_in_hierarchy(
                    self.data["get"]["hierarchy"][0],
                    id_to_find, self._add_item_below, new_id, new_type) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _add_item_below(self, child: Dict, current_entry: Dict, id_to_find: int, new_id: int, new_type: ComponentType):
        if id_to_find == child["id"]:
            child["children"].append({"id": new_id, "type": new_type.value, "children": []})
            Pub().pub("openWB/set/counter/get/hierarchy", self.data["get"]["hierarchy"])
            return True
        else:
            return False

    def __edit_element_in_hierarchy(self, current_entry: Dict, id_to_find: int, func: Callable, *args) -> bool:
        for child in current_entry["children"]:
            if func(child, current_entry, id_to_find, *args):
                return True
            else:
                if len(child["children"]) != 0:
                    if self.__edit_element_in_hierarchy(child, id_to_find, func, *args):
                        return True
        else:
            return False


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
                "daily_exported": 0,
                "daily_imported": 0}}
            self.num = index
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            # Wenn der Zähler keine Werte liefert, darf nicht geladen werden.
            connected_cps = data.data.counter_data["all"].get_chargepoints_of_counter(f'counter{self.num}')
            for cp in connected_cps:
                if self.data["get"]["fault_state"] == FaultStateLevel.ERROR:
                    data.data.cp_data[cp].data.set.loadmanagement_available = False
                else:
                    data.data.cp_data[cp].data.set.loadmanagement_available = True
            if self.data["get"]["fault_state"] == FaultStateLevel.ERROR:
                self.data["get"]["power"] = 0
                return

            # Nur beim EVU-Zähler wird auch die maximale Leistung geprüft.
            if f'counter{self.num}' == data.data.counter_data["all"].get_evu_counter():
                # max Leistung
                if self.data["get"]["power"] > 0:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_total_power"] \
                        - self.data["get"]["power"]
                else:
                    self.data["set"]["consumption_left"] = self.data["config"]["max_total_power"]
                log.debug(str(self.data["set"]["consumption_left"]) +
                          "W EVU-Leistung, die noch bezogen werden kann.")
            # Strom
            try:
                self.data["set"]["currents_used"] = self.data["get"]["currents"]
            except KeyError:
                log.warning(f"Zähler {self.num}: Einzelwerte für Zähler-Phasenströme unbekannt")
                self.data["set"]["state_str"] = "Das Lastmanagement regelt nur anhand der Gesamtleistung, da keine \
                    Phasenströme ermittelt werden konnten."
                Pub().pub("openWB/set/counter/"+str(self.num) + "/set/state_str",
                          self.data["set"]["state_str"])
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def put_stats(self):
        try:
            if f'counter{self.num}' == data.data.counter_data["all"].get_evu_counter():
                Pub().pub("openWB/set/counter/"+str(self.num)+"/set/consumption_left",
                          self.data["set"]["consumption_left"])
                log.debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def print_stats(self):
        try:
            log.debug(str(self.data["set"]["consumption_left"])+"W verbleibende EVU-Bezugs-Leistung")
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))
