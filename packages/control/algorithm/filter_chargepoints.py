# tested
import logging
import re
from typing import List, Optional, Tuple

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.load_protocol import Load

log = logging.getLogger(__name__)


def get_loads_by_mode_and_counter(chargemodes: Tuple[Tuple[Optional[str], str]],
                                  counter: str,
                                  full_power_considered: bool = True) -> List[Load]:
    loads_to_counter = data.data.counter_all_data.get_loads_of_counter(counter)
    # nur die Zahl aus dem String "cp1" und "consumer1" extrahieren
    loads_to_counter_ids = [int(re.search(r'\d+', load).group()) for load in loads_to_counter]
    loads_by_mode = get_loadmanagement_prios(chargemodes, full_power_considered)
    return list(filter(lambda load: load.num in loads_to_counter_ids, loads_by_mode))

# tested


def get_loadmanagement_prios(chargemodes: Tuple[Tuple[Optional[str], str]],
                             full_power_considered: bool = True) -> List[Load]:
    def _is_valid_for_chargemode(entity, chargemode, valid, valid_chargemode):
        """Helper function to validate entity against chargemode conditions."""
        return (entity.data.control_parameter.required_current != 0 and
                (entity.data.control_parameter.chargemode == chargemode[0] or chargemode[0] is None) and
                entity.data.control_parameter.submode == chargemode[1] and
                entity not in valid and entity not in valid_chargemode)

    def _process_chargemodes(power_filter_func):
        for chargemode in chargemodes:
            valid_chargemode = []
            for item in data.data.counter_all_data.data.get.loadmanagement_prios:
                if item["type"] == "ev":
                    for cp in data.data.cp_data.values():
                        if item["id"] == cp.data.config.ev and power_filter_func(cp):
                            if _is_valid_for_chargemode(cp, chargemode, valid, valid_chargemode):
                                valid_chargemode.append(cp)
                elif item["type"] == "consumer":
                    consumer = data.data.consumer_data[f"{item['type']}{item['id']}"]
                    if _is_valid_for_chargemode(consumer, chargemode, valid, valid_chargemode):
                        valid_chargemode.append(consumer)
            valid.extend(valid_chargemode)

    valid = []
    if full_power_considered:
        _process_chargemodes(lambda cp: cp.data.set.charging_ev_data.data.full_power is True)
        _process_chargemodes(lambda cp: cp.data.set.charging_ev_data.data.full_power is False)
    else:
        _process_chargemodes(lambda cp: True)
    return valid


def get_preferenced_chargepoint_charging(
        chargepoints: List[Chargepoint]) -> Tuple[List[Chargepoint], List[Chargepoint]]:
    preferenced_chargepoints_with_set_current = []
    preferenced_chargepoints_without_set_current = []
    for cp in chargepoints:
        if cp.data.set.target_current == 0:
            log.info(
                f"LP {cp.num}: Keine Zuteilung des Mindeststroms, daher keine weitere Berücksichtigung")
            preferenced_chargepoints_without_set_current.append(cp)
        elif cp.data.get.charge_state is False:
            log.info(
                f"LP {cp.num}: Lädt nicht, daher keine weitere Berücksichtigung")
            preferenced_chargepoints_without_set_current.append(cp)
        else:
            preferenced_chargepoints_with_set_current.append(cp)
    return preferenced_chargepoints_with_set_current, preferenced_chargepoints_without_set_current
