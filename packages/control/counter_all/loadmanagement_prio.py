import logging
from typing import Dict, List

from control.chargepoint.chargepoint import Chargepoint
from control.counter_all.counter_all_data import LoadmanagementPrioProtocol


log = logging.getLogger(__name__)


class LoadmanagementPrioMixin:
    def add_loadmanagement_prio_item(self: LoadmanagementPrioProtocol, type: str, id: int) -> None:
        self.data.get.loadmanagement_prios.append({"type": type, "id": id})

    def remove_loadmanagement_prio_item(self: LoadmanagementPrioProtocol, id: int) -> None:
        if self._remove_loadmanagement_prio_item(id, self.data.get.loadmanagement_prios) is False:
            raise IndexError(f"Element {id} konnte nicht in der Prioritätensteuerung gefunden werden.")

    def _remove_loadmanagement_prio_item(self: LoadmanagementPrioProtocol, id: int, entry: List[Dict]) -> bool:
        for item in entry:
            if item["type"] == "vehicle":
                if item["id"] == id:
                    entry.remove(item)
                    return True
            elif item["type"] == "group":
                removed_item = self._remove_loadmanagement_prio_item(id, item["children"])
                if removed_item and len(item["children"]) == 0:
                    entry.remove(item)
                if removed_item:
                    return True
        return False

    def sort_cps_by_loadmanagement_prios_nested(self: LoadmanagementPrioProtocol,
                                                filtered_cps: List[Chargepoint]) -> List[List[Chargepoint]]:
        sorted_cps = []
        for entry in self.data.get.loadmanagement_prios:
            if entry["type"] == "vehicle":
                grouped_cps = []
                for cp in filtered_cps:
                    if cp.data.config.ev == entry["id"]:
                        grouped_cps.append(cp)
                if len(grouped_cps) > 0:
                    sorted_cps.append(grouped_cps)
            elif entry["type"] == "group":
                grouped_cps = []
                for group_entry in entry["children"]:
                    for cp in filtered_cps:
                        if cp.data.config.ev == group_entry["id"]:
                            grouped_cps.append(cp)
                if len(grouped_cps) > 0:
                    sorted_cps.append(grouped_cps)
        return sorted_cps

    def sort_cps_by_loadmanagement_prios_flat(self: LoadmanagementPrioProtocol,
                                              filtered_cps: List[Chargepoint]) -> List[Chargepoint]:
        sorted_cps = []
        for entry in self.data.get.loadmanagement_prios:
            if entry["type"] == "vehicle":
                for cp in filtered_cps:
                    if cp.data.config.ev == entry["id"]:
                        sorted_cps.append(cp)
            elif entry["type"] == "group":
                for group_entry in entry["children"]:
                    for cp in filtered_cps:
                        if cp.data.config.ev == group_entry["id"]:
                            sorted_cps.append(cp)
        if len(sorted_cps) != len(filtered_cps):
            raise ValueError(
                "Fahrzeuge der Prioritätensteuerung konnten nicht korrekt den Ladepunkten zugeordnet werden.")
        return sorted_cps
