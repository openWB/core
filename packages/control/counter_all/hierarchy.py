import logging
import re
from typing import Callable, Dict, List, Union

from control import data
from control.counter_all.counter_all_data import HierarchyProtocol
from helpermodules.messaging import MessageType, pub_system_message
from modules.common.component_type import ComponentType, component_type_to_readable_text

log = logging.getLogger(__name__)


class HierarchyMixin:
    def get_all_elements_without_children(self: HierarchyProtocol, id: int) -> List[Dict]:
        self.childless = []
        self._get_all_elements_without_children_recursive(self.get_entry_of_element(id))
        return self.childless

    def _get_all_elements_without_children_recursive(self: HierarchyProtocol, child: Dict) -> None:
        for child in child["children"]:
            try:
                if len(child["children"]) != 0:
                    self._get_all_elements_without_children_recursive(child)
                else:
                    self.childless.append(child)
            except Exception:
                log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def get_loads_of_counter(self: HierarchyProtocol, counter: str) -> List[str]:
        """ gibt eine Liste der Ladepunkte, die in den folgenden Zweigen des Zählers sind, zurück.
        """
        self.connected_loads = []
        if counter == self.get_evu_counter_str():
            counter_object = self.data.get.hierarchy[0]
        else:
            counter_object = self._get_entry(
                self.data.get.hierarchy[0],
                int(counter[7:]),
                self._get_entry_of_element)
        try:
            self._get_all_loads_connected_to_counter(counter_object)
        except KeyError:
            # Kein Ladepunkt unter dem Zähler
            pass
        return self.connected_loads

    def _get_all_loads_connected_to_counter(self: HierarchyProtocol, child: Dict) -> None:
        """ Rekursive Funktion, die alle Ladepunkte ermittelt, die an den angegebenen Zähler angeschlossen sind.
        """
        # Alle Objekte der Ebene durchgehen
        for child in child["children"]:
            try:
                if child["type"] == ComponentType.CHARGEPOINT.value:
                    self.connected_loads.append(f"cp{child['id']}")
                elif child["type"] == ComponentType.CONSUMER.value:
                    self.connected_loads.append(f"consumer{child['id']}")
                # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
                elif len(child["children"]) != 0:
                    self._get_all_loads_connected_to_counter(child)
            except Exception:
                log.exception("Fehler in der allgemeinen Zähler-Klasse")

    def get_counters_to_check(self: HierarchyProtocol, num: int) -> List[str]:
        """ ermittelt alle Zähler im Zweig des Ladepunkts.
        """
        self.connected_counters = []
        self._get_all_counter_in_branch(self.data.get.hierarchy[0], num)
        return self.connected_counters

    def get_entry_of_element(self: HierarchyProtocol, id_to_find: int) -> Dict[str, List[Dict[str, Union[int, str]]]]:
        item = self._is_id_in_top_level(id_to_find)
        if item:
            return item
        else:
            return self._get_entry(self.data.get.hierarchy[0], id_to_find, self._get_entry_of_element)

    def get_entry_of_parent(self: HierarchyProtocol, id_to_find: int) -> Dict:
        if self._is_id_in_top_level(id_to_find):
            return {}
        for child in self.data.get.hierarchy[0]["children"]:
            if child["id"] == id_to_find:
                return self.data.get.hierarchy[0]
        else:
            return self._get_entry(self.data.get.hierarchy[0], id_to_find, self._get_entry_of_parent)

    def _is_id_in_top_level(self: HierarchyProtocol, id_to_find: int) -> Dict:
        for item in self.data.get.hierarchy:
            if item["id"] == id_to_find:
                return item
        else:
            return {}

    def _get_all_counter_in_branch(self: HierarchyProtocol, child: Dict, id_to_find: int) -> bool:
        """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle
        Zähler in diesem Pfad der Liste anhängt.
        """
        parent_id = child["id"]
        for child in child["children"]:
            if child["id"] == id_to_find:
                self.connected_counters.append(f"counter{parent_id}")
                return True
            if len(child["children"]) != 0:
                found = self._get_all_counter_in_branch(child, id_to_find)
                if found:
                    self.connected_counters.append(f"counter{parent_id}")
                    return True
        else:
            return False

    def _get_entry(self: HierarchyProtocol, child: Dict, id_to_find: int, func: Callable[[Dict, int], bool]) -> Dict:
        for child in child["children"]:
            found = func(child, id_to_find)
            if found:
                return child
            if len(child["children"]) != 0:
                entry = self._get_entry(child, id_to_find, func)
                if entry:
                    return entry
        else:
            return {}

    def _get_entry_of_element(self: HierarchyProtocol, child: Dict, id_to_find: int) -> bool:
        if child["id"] == id_to_find:
            return True
        else:
            return False

    def _get_entry_of_parent(self: HierarchyProtocol, child: Dict, id_to_find: int) -> bool:
        for child2 in child["children"]:
            if child2["id"] == id_to_find:
                return True
        else:
            return False

    def hierarchy_add_item_aside(self: HierarchyProtocol,
                                 new_id: int, new_type: ComponentType,
                                 id_to_find: int) -> None:
        """ ruft die rekursive Funktion zum Hinzufügen eines Zählers oder Ladepunkts in die Zählerhierarchie auf
        derselben Ebene wie das angegebene Element.
        """
        if self._is_id_in_top_level(id_to_find):
            self.data.get.hierarchy.append({"id": new_id, "type": new_type.value, "children": []})
        else:
            if (self._edit_element_in_hierarchy(
                    self.data.get.hierarchy[0],
                    id_to_find, self._add_item_aside, new_id, new_type) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _add_item_aside(self: HierarchyProtocol,
                        child: Dict,
                        current_entry: List,
                        id_to_find: int,
                        new_id: int,
                        new_type: ComponentType) -> bool:
        if id_to_find == child["id"]:
            current_entry["children"].append({"id": new_id, "type": new_type.value, "children": []})
            return True
        else:
            return False

    def hierarchy_remove_item(self: HierarchyProtocol, id_to_find: int, keep_children: bool = True) -> None:
        """ruft die rekursive Funktion zum Löschen eines Elements. Je nach Flag werden die Kinder gelöscht oder auf die
        Ebene des gelöschten Elements gehoben.
        """
        item = self._is_id_in_top_level(id_to_find)
        if item:
            if keep_children:
                self.data.get.hierarchy.extend(item["children"])
            self.data.get.hierarchy.remove(item)
        else:
            if (self._edit_element_in_hierarchy(
                    self.data.get.hierarchy[0],
                    id_to_find, self._remove_item, keep_children) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _remove_item(self: HierarchyProtocol, child: Dict, current_entry: Dict, id: str, keep_children: bool) -> bool:
        if id == child["id"]:
            if keep_children:
                current_entry["children"].extend(child["children"])
            current_entry["children"].remove(child)
            return True
        else:
            return False

    def hierarchy_add_item_below_evu(self: HierarchyProtocol, new_id: int, new_type: ComponentType) -> None:
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

    def hierarchy_add_item_below(self: HierarchyProtocol,
                                 new_id: int,
                                 new_type: ComponentType, id_to_find: int) -> None:
        """ruft die rekursive Funktion zum Hinzufügen eines Elements als Kind des angegebenen Elements.
        """
        item = self._is_id_in_top_level(id_to_find)
        if item:
            item["children"].append({"id": new_id, "type": new_type.value, "children": []})
        else:
            if (self._edit_element_in_hierarchy(
                    self.data.get.hierarchy[0],
                    id_to_find, self._add_item_below, new_id, new_type) is False):
                raise IndexError(f"Element {id_to_find} konnte nicht in der Hierarchie gefunden werden.")

    def _add_item_below(self: HierarchyProtocol,
                        child: Dict, current_entry: Dict,
                        id_to_find: int,
                        new_id: int,
                        new_type: ComponentType) -> bool:
        if id_to_find == child["id"]:
            child["children"].append({"id": new_id, "type": new_type.value, "children": []})
            return True
        else:
            return False

    def _edit_element_in_hierarchy(self: HierarchyProtocol,
                                   current_entry: Dict,
                                   id_to_find: int,
                                   func: Callable,
                                   *args) -> bool:
        for child in current_entry["children"]:
            if func(child, current_entry, id_to_find, *args):
                return True
            else:
                if len(child["children"]) != 0:
                    if self._edit_element_in_hierarchy(child, id_to_find, func, *args):
                        return True
        else:
            return False

    def get_list_of_elements_per_level(self: HierarchyProtocol) -> List[List[Dict[str, Union[int, str]]]]:
        elements_per_level: List[List[Dict[str, Union[int, str]]]] = []
        for item in self.data.get.hierarchy:
            list(zip(elements_per_level, self._get_list_of_elements_per_level(elements_per_level, item, 0)))
        return elements_per_level

    def _get_list_of_elements_per_level(self: HierarchyProtocol,
                                        elements_per_level: List[List[Dict[str, Union[int, str]]]],
                                        child: Dict,
                                        index: int) -> List:
        try:
            elements_per_level[index].extend([{"type": child["type"], "id": child["id"]}])
        except IndexError:
            elements_per_level.insert(index, [{"type": child["type"], "id": child["id"]}])
        for child in child["children"]:
            elements_per_level = self._get_list_of_elements_per_level(elements_per_level, child, index+1)
        return elements_per_level

    def validate_hierarchy(self: HierarchyProtocol):
        try:
            self._delete_obsolete_entries()
            self._add_missing_entries()
        except Exception:
            log.exception("Fehler bei der Validierung der Hierarchie")

    def _delete_obsolete_entries(self: HierarchyProtocol):
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

    def _add_missing_entries(self: HierarchyProtocol):
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
        try:
            self.get_id_evu_counter()
            check_and_add(ComponentType.BAT, data.data.bat_data)
            check_and_add(ComponentType.CHARGEPOINT, data.data.cp_data)
            check_and_add(ComponentType.INVERTER, data.data.pv_data)
        except TypeError:
            pub_system_message({}, ("Es konnte kein Zähler gefunden werden, der als EVU-Zähler an die Spitze des "
                               "Lastmanagements gesetzt werden kann. Bitte zuerst einen EVU-Zähler hinzufügen."),
                               MessageType.ERROR)
