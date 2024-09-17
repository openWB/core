"""Zähler-Logik
"""
import copy
from dataclasses import dataclass, field
import logging
import re
from typing import Callable, Dict, List, Optional, Tuple, Union

from control import data
from control.counter import Counter
from dataclass_utils.factories import empty_list_factory
from helpermodules.messaging import MessageType, pub_system_message
from helpermodules.pub import Pub
from modules.common.component_type import ComponentType, component_type_to_readable_text
from modules.common.fault_state import FaultStateLevel
from modules.common.simcount import SimCounter

log = logging.getLogger(__name__)


@dataclass
class Config:
    home_consumption_source_id: Optional[str] = field(
        default=None, metadata={"topic": "config/home_consumption_source_id"})
    consider_less_charging: bool = field(
        default=False, metadata={"topic": "config/consider_less_charging"})


def config_factory() -> Config:
    return Config()


@dataclass
class Set:
    loadmanagement_active: bool = field(
        default=False, metadata={"topic": "set/loadmanagement_active"})
    home_consumption: float = field(default=0, metadata={"topic": "set/home_consumption"})
    smarthome_power_excluded_from_home_consumption: float = field(
        default=0,
        metadata={"topic": "set/smarthome_power_excluded_from_home_consumption"})
    invalid_home_consumption: int = field(
        default=0, metadata={"topic": "set/invalid_home_consumption"})
    daily_yield_home_consumption: float = field(
        default=0, metadata={"topic": "set/daily_yield_home_consumption"})
    imported_home_consumption: float = field(
        default=0, metadata={"topic": "set/imported_home_consumption"})
    disengageable_smarthome_power: float = field(
        default=0, metadata={"topic": "set/disengageable_smarthome_power"})


@dataclass
class Get:
    hierarchy: List = field(default_factory=empty_list_factory, metadata={
                            "topic": "get/hierarchy"})


def get_factory() -> Get:
    return Get()


def set_factory() -> Set:
    return Set()


@dataclass
class CounterAllData:
    config: Config = field(default_factory=config_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)


class CounterAll:
    MISSING_EVU_COUNTER = "Bitte erst einen EVU-Zähler konfigurieren."

    def __init__(self):
        self.data = CounterAllData()
        # Hilfsvariablen für die rekursiven Funktionen
        self.connected_counters = []
        self.connected_chargepoints = []
        self.childless = []
        self.sim_counter = SimCounter("", "", prefix="bezug")
        self.sim_counter.topic = "openWB/set/counter/set/"

    def get_evu_counter(self) -> Counter:
        return data.data.counter_data[f"counter{self.get_id_evu_counter()}"]

    def get_evu_counter_str(self) -> str:
        return f"counter{self.get_id_evu_counter()}"

    def get_id_evu_counter(self) -> int:
        try:
            if ComponentType.COUNTER.value == self.data.get.hierarchy[0]["type"]:
                return self.data.get.hierarchy[0]['id']
            else:
                raise TypeError
        except Exception:
            log.error(
                "Ohne Konfiguration eines EVU-Zählers an der Spitze der Hierarchie ist keine Regelung und keine Ladung "
                "möglich.")
            raise

    def set_home_consumption(self) -> None:
        try:
            self._validate_home_consumption_counter()
            home_consumption, elements = self._calc_home_consumption()
            if home_consumption < 0:
                log.error(
                    f"Ungültiger Hausverbrauch: {home_consumption}W, Berücksichtigte Komponenten neben EVU {elements}")
                if self.data.config.home_consumption_source_id is None:
                    hc_counter_source = self.get_evu_counter_str()
                else:
                    hc_counter_source = f"counter{self.data.config.home_consumption_source_id}"
                hc_counter_data = data.data.counter_data[hc_counter_source].data
                if hc_counter_data.get.fault_state == FaultStateLevel.NO_ERROR:
                    hc_counter_data.get.fault_state = FaultStateLevel.WARNING.value
                    hc_counter_data.get.fault_str = ("Hinweis: Es gibt mehr Stromerzeuger im Haus als in der openWB "
                                                     "eingetragen sind. Der Hausverbrauch kann nicht korrekt berechnet "
                                                     "werden. Dies hat auf die PV-Überschussladung keine negativen "
                                                     "Auswirkungen.")
                if self.data.set.invalid_home_consumption < 3:
                    self.data.set.invalid_home_consumption += 1
                    return
                else:
                    home_consumption = 0
            else:
                self.data.set.invalid_home_consumption = 0
            self.data.set.home_consumption = home_consumption
            imported, _ = self.sim_counter.sim_count(self.data.set.home_consumption)
            self.data.set.imported_home_consumption = imported
        except Exception:
            log.exception("Fehler in der allgemeinen Zähler-Klasse")

    EVU_IS_HC_COUNTER_ERROR = ("Der EVU-Zähler kann nicht als Quelle für den Hausverbrauch verwendet werden. Meist ist "
                               "der Zähler am EVU-Punkt installiert, dann muss im Lastmanagement unter Hausverbrauch"
                               " 'von openWB berechnen' ausgewählt werden. Wenn der Zähler im Hausverbrauchszweig "
                               "installiert ist, einen virtuellen Zähler anlegen und im Lastmanagement ganz links "
                               "anordnen.")

    def _validate_home_consumption_counter(self):
        if self.data.config.home_consumption_source_id is not None:
            if self.data.config.home_consumption_source_id == self.get_id_evu_counter():
                hc_counter_data = data.data.counter_data[self.get_evu_counter_str()].data
                hc_counter_data.get.fault_state = FaultStateLevel.ERROR.value
                hc_counter_data.get.fault_str = self.EVU_IS_HC_COUNTER_ERROR
                evu_counter = self.get_id_evu_counter()
                Pub().pub(f"openWB/set/counter/{evu_counter}/get/fault_state",
                          hc_counter_data.get.fault_state)
                Pub().pub(f"openWB/set/counter/{evu_counter}/get/fault_str",
                          hc_counter_data.get.fault_str)
                raise Exception(self.EVU_IS_HC_COUNTER_ERROR)

    def _calc_home_consumption(self) -> Tuple[float, List]:
        power = 0
        if self.data.config.home_consumption_source_id is None:
            id_source = self.get_id_evu_counter()
        else:
            id_source = self.data.config.home_consumption_source_id
        elements_to_sum_up = self.get_elements_for_downstream_calculation(id_source)
        for element in elements_to_sum_up:
            if element["type"] == ComponentType.CHARGEPOINT.value:
                component = data.data.cp_data[f"cp{element['id']}"]
            elif element["type"] == ComponentType.BAT.value:
                component = data.data.bat_data[f"bat{element['id']}"]
            elif element["type"] == ComponentType.COUNTER.value:
                component = data.data.counter_data[f"counter{element['id']}"]
            elif element["type"] == ComponentType.INVERTER.value:
                component = data.data.pv_data[f"pv{element['id']}"]

            if component.data.get.fault_state < 2:
                power += component.data.get.power
            else:
                log.warning(
                    f"Komponente {element['type']}{component.num} ist im Fehlerzustand und wird nicht berücksichtigt.")
        evu = data.data.counter_data[f"counter{id_source}"].data.get.power
        return evu - power - self.data.set.smarthome_power_excluded_from_home_consumption, elements_to_sum_up

    def _add_hybrid_bat(self, id: int) -> List:
        elements = []
        inverter_children = self.get_entry_of_element(id)["children"]
        for child in inverter_children:
            if child["type"] == ComponentType.BAT.value:
                elements.append(child)
        return elements

    def get_elements_for_downstream_calculation(self, id: int):
        """returns a list of elements that are relevant for the calculation of the counter values based on the
        downstream components, eg home consumption or virtual counter."""
        elements = copy.deepcopy(self.get_entry_of_element(id)["children"])
        elements_to_sum_up = elements
        for element in elements:
            if element["type"] == ComponentType.INVERTER.value:
                elements_to_sum_up.extend(self._add_hybrid_bat(element['id']))
        return elements_to_sum_up

    # Hierarchie analysieren

    def get_all_elements_without_children(self, id: int) -> List[Dict]:
        self.childless.clear()
        self.get_all_elements_without_children_recursive(self.get_entry_of_element(id))
        return self.childless

    def get_all_elements_without_children_recursive(self, child: Dict) -> None:
        for child in child["children"]:
            try:
                if len(child["children"]) != 0:
                    self.get_all_elements_without_children_recursive(child)
                else:
                    self.childless.append(child)
            except Exception:
                log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def get_chargepoints_of_counter(self, counter: str) -> List[str]:
        """ gibt eine Liste der Ladepunkte, die in den folgenden Zweigen des Zählers sind, zurück.
        """
        self.connected_chargepoints.clear()
        if counter == self.get_evu_counter_str():
            counter_object = self.data.get.hierarchy[0]
        else:
            counter_object = self.__get_entry(
                self.data.get.hierarchy[0],
                int(counter[7:]),
                self.__get_entry_of_element)
        try:
            self._get_all_cp_connected_to_counter(counter_object)
        except KeyError:
            # Kein Ladepunkt unter dem Zähler
            pass
        return self.connected_chargepoints

    def _get_all_cp_connected_to_counter(self, child: Dict) -> None:
        """ Rekursive Funktion, die alle Ladepunkte ermittelt, die an den angegebenen Zähler angeschlossen sind.
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

    def get_counters_to_check(self, num: int) -> List[str]:
        """ ermittelt alle Zähler im Zweig des Ladepunkts.
        """
        self.connected_counters.clear()
        self.__get_all_counter_in_branch(self.data.get.hierarchy[0], num)
        return self.connected_counters

    def get_entry_of_element(self, id_to_find: int) -> Dict:
        item = self.__is_id_in_top_level(id_to_find)
        if item:
            return item
        else:
            return self.__get_entry(self.data.get.hierarchy[0], id_to_find, self.__get_entry_of_element)

    def get_entry_of_parent(self, id_to_find: int) -> Dict:
        if self.__is_id_in_top_level(id_to_find):
            return {}
        for child in self.data.get.hierarchy[0]["children"]:
            if child["id"] == id_to_find:
                return self.data.get.hierarchy[0]
        else:
            return self.__get_entry(self.data.get.hierarchy[0], id_to_find, self.__get_entry_of_parent)

    def __is_id_in_top_level(self, id_to_find: int) -> Dict:
        for item in self.data.get.hierarchy:
            if item["id"] == id_to_find:
                return item
        else:
            return {}

    def __get_all_counter_in_branch(self, child: Dict, id_to_find: int) -> bool:
        """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle
        Zähler in diesem Pfad der Liste anhängt.
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
            self.data.get.hierarchy.append({"id": new_id, "type": new_type.value, "children": []})
        else:
            if (self.__edit_element_in_hierarchy(
                    self.data.get.hierarchy[0],
                    id_to_find, self._add_item_aside, new_id, new_type) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _add_item_aside(
            self, child: Dict, current_entry: Dict, id_to_find: int, new_id: int, new_type: ComponentType) -> bool:
        if id_to_find == child["id"]:
            current_entry["children"].append({"id": new_id, "type": new_type.value, "children": []})
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
                self.data.get.hierarchy.extend(item["children"])
            self.data.get.hierarchy.remove(item)
        else:
            if (self.__edit_element_in_hierarchy(
                    self.data.get.hierarchy[0],
                    id_to_find, self._remove_item, keep_children) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _remove_item(self, child: Dict, current_entry: Dict, id: str, keep_children: bool) -> bool:
        if id == child["id"]:
            if keep_children:
                current_entry["children"].extend(child["children"])
            current_entry["children"].remove(child)
            return True
        else:
            return False

    def hierarchy_add_item_below_evu(self, new_id: int, new_type: ComponentType) -> None:
        try:
            self.hierarchy_add_item_below(new_id, new_type, self.get_id_evu_counter())
        except (TypeError, IndexError):
            if new_type == ComponentType.COUNTER:
                # es gibt noch keinen EVU-Zähler
                hierarchy = [{
                    "id": new_id,
                    "type": ComponentType.COUNTER.value,
                    "children": self.data.get.hierarchy
                }]
                self.data.get.hierarchy = hierarchy
            else:
                raise ValueError(self.MISSING_EVU_COUNTER)

    def hierarchy_add_item_below(self, new_id: int, new_type: ComponentType, id_to_find: int) -> None:
        """ruft die rekursive Funktion zum Hinzufügen eines Elements als Kind des angegebenen Elements.
        """
        item = self.__is_id_in_top_level(id_to_find)
        if item:
            item["children"].append({"id": new_id, "type": new_type.value, "children": []})
        else:
            if (self.__edit_element_in_hierarchy(
                    self.data.get.hierarchy[0],
                    id_to_find, self._add_item_below, new_id, new_type) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _add_item_below(
            self, child: Dict, current_entry: Dict, id_to_find: int, new_id: int, new_type: ComponentType) -> bool:
        if id_to_find == child["id"]:
            child["children"].append({"id": new_id, "type": new_type.value, "children": []})
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

    def get_list_of_elements_per_level(self) -> List[List[Dict[str, Union[int, str]]]]:
        elements_per_level: List[List[Dict[str, Union[int, str]]]] = []
        for item in self.data.get.hierarchy:
            list(zip(elements_per_level, self._get_list_of_elements_per_level(elements_per_level, item, 0)))
        return elements_per_level

    def _get_list_of_elements_per_level(self, elements_per_level: List, child: Dict, index: int) -> List:
        try:
            elements_per_level[index].extend([{"type": child["type"], "id": child["id"]}])
        except IndexError:
            elements_per_level.insert(index, [{"type": child["type"], "id": child["id"]}])
        for child in child["children"]:
            elements_per_level = self._get_list_of_elements_per_level(elements_per_level, child, index+1)
        return elements_per_level

    def validate_hierarchy(self):
        try:
            self._delete_obsolete_entries()
            self._add_missing_entries()
        except Exception:
            log.exception("Fehler bei der Validierung der Hierarchie")

    def _delete_obsolete_entries(self):
        def check_and_remove(name, type_name: ComponentType, data_structure):
            if element["type"] == type_name.value:
                if f"{name}{element['id']}" not in data_structure:
                    self.hierarchy_remove_item(element["id"])
                    pub_system_message({}, f"{component_type_to_readable_text(type_name)} mit ID {element['id']} wurde"
                                       " aus der Hierarchie entfernt, da keine gültige Konfiguration gefunden wurde.",
                                       MessageType.WARNING)

        for level in self.get_list_of_elements_per_level():
            for element in level:
                check_and_remove("bat", ComponentType.BAT, data.data.bat_data)
                check_and_remove("counter", ComponentType.COUNTER, data.data.counter_data)
                check_and_remove("cp", ComponentType.CHARGEPOINT, data.data.cp_data)
                check_and_remove("pv", ComponentType.INVERTER, data.data.pv_data)

    def _add_missing_entries(self):
        def check_and_add(type_name: ComponentType, data_structure):
            for entry in data_structure:
                break_flag = False
                re_result = re.search("[0-9]+", entry)
                if re_result is not None:
                    entry_num = int(re_result.group())
                for level in self.get_list_of_elements_per_level():
                    for element in level:
                        if entry_num == element["id"] and element["type"] == type_name.value:
                            break_flag = True
                            break
                    if break_flag:
                        break
                else:
                    try:
                        self.hierarchy_add_item_below_evu(entry_num, type_name)
                    except ValueError:
                        pub_system_message({}, "Die Struktur des Lastmanagements ist nicht plausibel. Bitte prüfe die "
                                           "Konfiguration und Anordnung der Komponenten in der Hierarchie.",
                                           MessageType.WARNING)

                    pub_system_message({}, f"{component_type_to_readable_text(type_name)} mit ID {element['id']} wurde"
                                       " in der Struktur des Lastmanagements hinzugefügt, da kein Eintrag in der "
                                       "Struktur gefunden wurde. Bitte prüfe die Anordnung der Komponenten in der "
                                       "Struktur.",
                                       MessageType.WARNING)

        # Falls EVU-Zähler fehlt, zuerst hinzufügen.
        check_and_add(ComponentType.COUNTER, data.data.counter_data)
        check_and_add(ComponentType.BAT, data.data.bat_data)
        check_and_add(ComponentType.CHARGEPOINT, data.data.cp_data)
        check_and_add(ComponentType.INVERTER, data.data.pv_data)


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
