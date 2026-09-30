# tested
import logging
import re
from typing import Iterator, List, Optional, Tuple

from control import data
from control.chargemode import Chargemode
from control.consumer.consumer import Consumer
from control.consumer.usage import ConsumerUsage
from control.load import get_load_str
from control.load_protocol import Load

log = logging.getLogger(__name__)


def filter_grouped_loads_by_mode_and_counter(grouped_loads: List[Load],
                                             chargemodes: Tuple[Tuple[Optional[str], str]],
                                             counter: str) -> List[Load]:
    filtered_grouped_loads = list(grouped_loads)

    filtered_grouped_loads = filter_loads_by_chargemodes(filtered_grouped_loads, chargemodes)
    filtered_grouped_loads = _filter_active_loads(filtered_grouped_loads)

    loads_to_counter = data.data.counter_all_data.get_loads_of_counter(counter)
    # nur die Zahl aus dem String "cp1" und "consumer2" extrahieren
    loads_to_counter_ids = [int(re.search(r'\d+', load).group()) for load in loads_to_counter]

    valid_loads: List[Load] = []
    for load in filtered_grouped_loads:
        if load.num in loads_to_counter_ids:
            valid_loads.append(load)

    return valid_loads


def _get_consumer_by_prio_item(item: dict) -> Optional[Consumer]:
    """Liefert den Verbraucher zu einem Eintrag der Prioritätensteuerung.

    Ein Eintrag kann kurzzeitig auf einen bereits gelöschten Verbraucher verweisen, wenn dessen Entfernung
    aus der Prioritätensteuerung fehlgeschlagen ist. Ein einzelner solcher Karteileichen-Eintrag darf nicht
    die komplette Regelung für alle Ladepunkte zum Absturz bringen.
    """
    consumer = data.data.consumer_data.get(f"{item['type']}{item['id']}")
    if consumer is None:
        log.warning(f"Verbraucher {item['id']} aus der Prioritätensteuerung existiert nicht (mehr), "
                    "wird ignoriert.")
    return consumer


def filter_loads_by_chargemodes(grouped_loads: List[Load],
                                chargemodes: Tuple[Tuple[Optional[str], str]]) -> List[Load]:
    filtered_grouped_loads: List[Load] = []
    for load in grouped_loads:
        for chargemode in chargemodes:
            if ((load.data.control_parameter.chargemode == chargemode[0] or chargemode[0] is None) and
                    load.data.control_parameter.submode == chargemode[1]):
                filtered_grouped_loads.append(load)
                break

    return filtered_grouped_loads


def _filter_active_loads(grouped_loads: List[Load]) -> List[Load]:
    active_loads: List[Load] = []
    for load in grouped_loads:
        if load.data.control_parameter.required_current != 0:
            active_loads.append(load)

    return active_loads


def group_loads_generator() -> Iterator[List[Load]]:
    for item in data.data.counter_all_data.data.get.loadmanagement_prios:
        if item["type"] == "group":
            sub_valid_chargemode: List[Load] = []
            for group_item in item["children"]:
                if group_item["type"] == "vehicle":
                    for cp in data.data.cp_data.values():
                        if group_item["id"] == cp.data.config.ev:
                            sub_valid_chargemode.append(cp)
                elif group_item["type"] == "consumer":
                    consumer = _get_consumer_by_prio_item(group_item)
                    if consumer is not None:
                        sub_valid_chargemode.append(consumer)
            yield sub_valid_chargemode
        if item["type"] == "vehicle":
            for cp in data.data.cp_data.values():
                if item["id"] == cp.data.config.ev:
                    yield [cp]
        elif item["type"] == "consumer":
            consumer = _get_consumer_by_prio_item(item)
            if consumer is not None:
                yield [consumer]


def _group_loads_by_chargemode(chargemodes: Tuple[Tuple[Optional[str], str]],
                               filter_func) -> List[Load]:
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
                        consumer = _get_consumer_by_prio_item(group_item)
                        if consumer is not None and filter_func(consumer, chargemode, flat_loads):
                            sub_valid_chargemode.append(consumer)
                            flat_loads.append(consumer)
            if item["type"] == "vehicle":
                for cp in data.data.cp_data.values():
                    if item["id"] == cp.data.config.ev:
                        if filter_func(cp, chargemode, flat_loads):
                            flat_loads.append(cp)
            elif item["type"] == "consumer":
                consumer = _get_consumer_by_prio_item(item)
                if consumer is not None and filter_func(consumer, chargemode, flat_loads):
                    flat_loads.append(consumer)
    return flat_loads


def get_loads_by_chargemodes(chargemodes: Tuple[Tuple[Optional[Chargemode], Chargemode]]) -> List[Load]:
    def _is_valid_for_chargemode(entity, chargemode, valid):
        """Helper function to validate entity against chargemode conditions."""
        return ((entity.data.control_parameter.chargemode == chargemode[0] or chargemode[0] is None) and
                entity.data.control_parameter.submode == chargemode[1] and
                entity not in valid)

    return _group_loads_by_chargemode(chargemodes, _is_valid_for_chargemode)


def get_preferenced_load_charging(
        grouped_loads: List[Load]) -> Tuple[List[Load], List[Load]]:
    preferenced_loads_without_set_current: List[Load] = []
    valid_group: List[Load] = []
    for load in grouped_loads:
        if load.data.set.target_current == 0:
            log.info(f"{get_load_str(load)}: "
                     f"Keine Zuteilung des Mindeststroms, daher keine weitere Berücksichtigung")
            preferenced_loads_without_set_current.append(load)
        elif load.data.get.charge_state is False:
            log.info(f"{get_load_str(load)}: Lädt nicht, daher keine weitere Berücksichtigung")
            preferenced_loads_without_set_current.append(load)
        elif (isinstance(load, Consumer) and
                load.data.usage.type in [ConsumerUsage.CONTINUOUS, ConsumerUsage.SUSPENDABLE_ONOFF]):
            log.info(f"Verbraucher {load.num}: Verbrauchsart {load.data.usage.type} führt zu keiner weiteren "
                     "Berücksichtigung")
            preferenced_loads_without_set_current.append(load)
        else:
            valid_group.append(load)
    return valid_group, preferenced_loads_without_set_current


def filtered_loads_to_str(loads: List[Load]) -> str:
    return ", ".join([get_load_str(load) for load in loads])
