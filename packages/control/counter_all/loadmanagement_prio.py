import logging
from typing import AbstractSet, Dict, Generator, List, Tuple

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.consumer.usage import ConsumerUsage, NOT_CONTROLLED
from control.counter_all.counter_all_data import LoadmanagementPrioProtocol
from helpermodules.messaging import MessageType, pub_system_message
from modules.common.component_type import ComponentType, component_type_to_readable_text


log = logging.getLogger(__name__)


class LoadmanagementPrioMixin:
    def validate_loadmanagement_prios(self: LoadmanagementPrioProtocol) -> None:
        try:
            valid_ids = {
                ComponentType.VEHICLE: {vehicle.num for vehicle in data.data.ev_data.values()},
                ComponentType.CONSUMER: {
                    consumer.num for consumer in data.data.consumer_data.values()
                    if consumer.data.usage.type not in NOT_CONTROLLED
                },
            }

            self._remove_obsolete_loadmanagement_prio_entries(self.data.get.loadmanagement_prios, valid_ids)
            self._add_missing_loadmanagement_prio_entries(self.data.get.loadmanagement_prios, valid_ids)

        except Exception:
            log.exception("Fehler bei der Validierung der Prioritätensteuerung")

    def _remove_obsolete_loadmanagement_prio_entries(
            self, entries: List[Dict], valid_ids: Dict[ComponentType, AbstractSet[int]]) -> None:
        for entry in entries.copy():
            if entry["type"] == "group":
                children = entry["children"]
                had_children = bool(children)
                self._remove_obsolete_loadmanagement_prio_entries(children, valid_ids)
                if had_children and not children:
                    entries.remove(entry)
            else:
                for type_name, ids in valid_ids.items():
                    if entry["type"] == type_name.value and entry["id"] not in ids:
                        entries.remove(entry)
                        if type_name == ComponentType.CONSUMER and any(
                                consumer.num == entry["id"] for consumer in data.data.consumer_data.values()):
                            reason = "er nicht durch openWB gesteuert wird."
                        else:
                            reason = "keine gültige Konfiguration gefunden wurde"
                        pub_system_message(
                            {}, f"{component_type_to_readable_text(type_name)} mit ID {entry['id']} wurde "
                            f"aus der Prioritätensteuerung entfernt, da {reason}.", MessageType.WARNING)

    def _add_missing_loadmanagement_prio_entries(
            self, entries: List[Dict], valid_ids: Dict[ComponentType, AbstractSet[int]]) -> None:
        for type_name, ids in valid_ids.items():
            for id in ids:
                if not self._has_loadmanagement_prio_item(type_name, id, entries):
                    self.add_loadmanagement_prio_item(type_name, id)
                    pub_system_message(
                        {}, f"{component_type_to_readable_text(type_name)} mit ID {id} wurde "
                        "der Prioritätensteuerung hinzugefügt.", MessageType.INFO)

    def add_loadmanagement_prio_item(self: LoadmanagementPrioProtocol, type: ComponentType, id: int) -> None:
        self.data.get.loadmanagement_prios.append({"type": type.value, "id": id})

    def update_consumer_loadmanagement_prio(
            self: LoadmanagementPrioProtocol, consumer_id: int, usage_type: ConsumerUsage) -> bool:
        consumer_in_prios = self._has_loadmanagement_prio_item(
            ComponentType.CONSUMER, consumer_id, self.data.get.loadmanagement_prios)
        if usage_type in NOT_CONTROLLED:
            if consumer_in_prios:
                self.remove_loadmanagement_prio_item(ComponentType.CONSUMER, consumer_id)
                return True
        elif consumer_in_prios is False:
            self.add_loadmanagement_prio_item(ComponentType.CONSUMER, consumer_id)
            return True
        return False

    def _has_loadmanagement_prio_item(self: LoadmanagementPrioProtocol,
                                      type: ComponentType,
                                      id: int,
                                      entries: List[Dict]) -> bool:
        for entry in entries:
            if entry["type"] == type.value and entry["id"] == id:
                return True
            if entry["type"] == "group" and self._has_loadmanagement_prio_item(type, id, entry["children"]):
                return True
        return False

    def remove_loadmanagement_prio_item(self: LoadmanagementPrioProtocol, type: ComponentType, id: int) -> None:
        if self._remove_loadmanagement_prio_item(type, id, self.data.get.loadmanagement_prios) is False:
            # Kein Grund, die Löschung des restlichen Elements (Topics, Hierarchie) abzubrechen, wenn der
            # Eintrag in der Prioritätensteuerung schon fehlt.
            log.warning(f"Element {type.value}/{id} konnte nicht in der Prioritätensteuerung gefunden werden.")

    def _remove_loadmanagement_prio_item(self: LoadmanagementPrioProtocol,
                                         type: ComponentType,
                                         id: int,
                                         entry: List[Dict]) -> bool:
        for item in entry:
            if item["type"] == type.value and item["id"] == id:
                entry.remove(item)
                return True
            elif item["type"] == "group":
                removed_item = self._remove_loadmanagement_prio_item(type, id, item["children"])
                if removed_item and len(item["children"]) == 0:
                    entry.remove(item)
                if removed_item:
                    return True
        return False

    def generator_cps_by_loadmanagement_prios(
        self: LoadmanagementPrioProtocol,
            filtered_cps: List[Chargepoint]) -> Generator[Tuple[Chargepoint, List[Chargepoint]], None, None]:
        sorted_cps = self.sort_cps_by_loadmanagement_prios_nested(filtered_cps)
        log.debug("Ladepunkte sortiert nach Prioritätensteuerung: ")
        log.debug([[f"LP {cp.num}" for cp in group] for group in sorted_cps])
        for group in sorted_cps:
            cp: Chargepoint
            while len(group) > 0:
                cp = group[0]
                yield cp, group.copy()
                group.pop(0)

    def sort_cps_by_loadmanagement_prios_nested(self: LoadmanagementPrioProtocol,
                                                filtered_cps: List[Chargepoint]) -> List[List[Chargepoint]]:
        sorted_cps = []
        for entry in self.data.get.loadmanagement_prios:
            if entry["type"] == "vehicle" or entry["type"] == "consumer":
                grouped_cps = []
                for cp in filtered_cps:
                    if cp.data.config.ev == entry["id"]:
                        grouped_cps.append(cp)
                if len(grouped_cps) > 0:
                    sorted_cps.append(grouped_cps)
            elif entry["type"] == "group":
                sorted_grouped_cps = []
                for group_entry in entry["children"]:
                    grouped_cps = []
                    for cp in filtered_cps:
                        if cp.data.config.ev == group_entry["id"]:
                            grouped_cps.append(cp)
                    sorted_grouped_cps.extend(grouped_cps)
                if len(sorted_grouped_cps) > 0:
                    sorted_cps.append(sorted_grouped_cps)
        return sorted_cps
