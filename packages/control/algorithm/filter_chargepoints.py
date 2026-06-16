# tested
import logging
import re
from typing import List, Optional, Tuple

from control import data
from control.chargemode import Chargemode
from control.chargepoint.chargepoint import Chargepoint
from control.load_protocol import Load

log = logging.getLogger(__name__)


def get_grouped_loads_by_mode_and_counter(chargemodes: Tuple[Tuple[Optional[str], str]],
                                          counter: str) -> List[List[Load]]:
    loads_to_counter = data.data.counter_all_data.get_loads_of_counter(counter)
    # nur die Zahl aus dem String "cp1" und "consumer2" extrahieren
    loads_to_counter_ids = [int(re.search(r'\d+', load).group()) for load in loads_to_counter]

    def _is_valid_for_chargemode(entity: Load,
                                 chargemode: Tuple[Optional[str], str],
                                 valid: List[Load]) -> bool:
        """Helper function to validate entity against chargemode conditions."""
        return (entity.data.control_parameter.required_current != 0 and
                (entity.data.control_parameter.chargemode == chargemode[0] or chargemode[0] is None) and
                entity.data.control_parameter.submode == chargemode[1] and
                entity not in valid and
                entity.num in loads_to_counter_ids)

    return _group_loads_by_chargemode(chargemodes, _is_valid_for_chargemode)[1]


def _group_loads_by_chargemode(chargemodes: Tuple[Tuple[Optional[str], str]],
                               filter_func) -> Tuple[List[Load], List[List[Load]]]:
    grouped_loads: List[List[Load]] = []
    flat_loads: List[Load] = []
    for chargemode in chargemodes:
        for item in data.data.counter_all_data.data.get.loadmanagement_prios:
            if item["type"] == "group":
                sub_valid_chargemode: List[Load] = []
                for group_item in item["children"]:
                    if group_item["type"] == "vehicle":
                        for cp in data.data.cp_data.values():
                            if group_item["id"] == cp.data.config.ev:
                                if filter_func(cp, chargemode, flat_loads):
                                    sub_valid_chargemode.append(cp)
                                    flat_loads.append(cp)
                    elif group_item["type"] == "consumer":
                        consumer = data.data.consumer_data[f"{group_item['type']}{group_item['id']}"]
                        if filter_func(consumer, chargemode, flat_loads):
                            sub_valid_chargemode.append(consumer)
                            flat_loads.append(consumer)
                grouped_loads.append(sub_valid_chargemode)
            if item["type"] == "vehicle":
                for cp in data.data.cp_data.values():
                    if item["id"] == cp.data.config.ev:
                        if filter_func(cp, chargemode, flat_loads):
                            grouped_loads.append([cp])
                            flat_loads.append(cp)
            elif item["type"] == "consumer":
                consumer = data.data.consumer_data[f"{item['type']}{item['id']}"]
                if filter_func(consumer, chargemode, flat_loads):
                    grouped_loads.append([consumer])
                    flat_loads.append(consumer)
    return flat_loads, grouped_loads


def get_loads_by_chargemodes(chargemodes: Tuple[Tuple[Optional[Chargemode], Chargemode]]) -> List[Load]:
    def _is_valid_for_chargemode(entity, chargemode, valid):
        """Helper function to validate entity against chargemode conditions."""
        return (entity.data.control_parameter.required_current != 0 and
                (entity.data.control_parameter.chargemode == chargemode[0] or chargemode[0] is None) and
                entity.data.control_parameter.submode == chargemode[1] and
                entity not in valid)

    return _group_loads_by_chargemode(chargemodes, _is_valid_for_chargemode)[0]


def get_preferenced_load_charging(
        grouped_loads: List[List[Load]]) -> Tuple[List[List[Load]], List[Load]]:
    preferenced_loads_without_set_current: List[Load] = []
    for group in grouped_loads:
        valid_group: List[Load] = []
        for load in group:
            if load.data.set.target_current == 0:
                log.info(f"{'LP' if isinstance(load, Chargepoint) else 'Verbraucher'} {load.num}: "
                         f"Keine Zuteilung des Mindeststroms, daher keine weitere Berücksichtigung")
                preferenced_loads_without_set_current.append(load)
            elif load.data.get.charge_state is False:
                log.info(f"{'LP' if isinstance(load, Chargepoint) else 'Verbraucher'} {load.num}: "
                         f"Lädt nicht, daher keine weitere Berücksichtigung")
                preferenced_loads_without_set_current.append(load)
            else:
                valid_group.append(load)
        group[:] = valid_group
    return grouped_loads, preferenced_loads_without_set_current


def filtered_loads_to_str(loads: List[Load]) -> str:
    return ", ".join([f"{'LP' if isinstance(load, Chargepoint) else 'Verbraucher'}{load.num}" for load in loads])
