import logging
from typing import Dict, Generator, List, Tuple

from control.chargepoint.chargepoint import Chargepoint
from control.consumer.usage import ConsumerUsage
from control.counter_all.counter_all_data import LoadmanagementPrioProtocol
from modules.common.component_type import ComponentType


log = logging.getLogger(__name__)


class LoadmanagementPrioMixin:
    def add_loadmanagement_prio_item(self: LoadmanagementPrioProtocol, type: ComponentType, id: int) -> None:
        self.data.get.loadmanagement_prios.append({"type": type.value, "id": id})

    def update_consumer_loadmanagement_prio(
            self: LoadmanagementPrioProtocol, consumer_id: int, usage_type: ConsumerUsage) -> None:
        consumer_in_prios = self._has_loadmanagement_prio_item(
            ComponentType.CONSUMER, consumer_id, self.data.get.loadmanagement_prios)
        if usage_type == ConsumerUsage.METER_ONLY:
            if consumer_in_prios:
                self.remove_loadmanagement_prio_item(ComponentType.CONSUMER, consumer_id)
        elif consumer_in_prios is False:
            self.add_loadmanagement_prio_item(ComponentType.CONSUMER, consumer_id)

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
