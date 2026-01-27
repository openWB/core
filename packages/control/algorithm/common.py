import logging
from typing import Iterable, List, Optional, Tuple

from control import data
from control.algorithm.filter_chargepoints import get_loadmanagement_prios
from control.algorithm.utils import get_medium_charging_current
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.load_protocol import Load
from helpermodules.phase_handling import voltages_mean
from helpermodules.timecheck import check_timestamp
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


LESS_CHARGING_TIMEOUT = 60

# tested


def reset_current():
    for load in list(data.data.cp_data.values()) + list(data.data.consumer_data.values()):
        try:
            load.data.set.current = None
            load.data.set.target_current = 0
        except Exception:
            log.exception(f"Fehler im Algorithmus-Modul für "
                          f"{'Ladepunkt' if isinstance(load, Chargepoint) else 'Verbraucher'}{load.num}")


def reset_current_by_chargemode(chargemodes: Tuple[Tuple[Optional[str], str]]) -> None:
    for load in get_loadmanagement_prios(chargemodes):
        load.data.set.current = None


def counter_generator() -> Iterable[Counter]:
    levels = data.data.counter_all_data.get_list_of_elements_per_level()
    for level in reversed(levels):
        for element in level:
            if element["type"] == ComponentType.COUNTER.value:
                counter = data.data.counter_data[f"counter{element['id']}"]
                yield counter


# tested


def get_min_current(load: Load) -> Tuple[List[float], List[int]]:
    min_currents = [0.0]*3
    counts = [0]*3
    required_currents = load.data.control_parameter.required_currents
    for i in range(3):
        if required_currents[i] != 0:
            counts[i] += 1
            min_currents[i] = load.data.control_parameter.min_current
        else:
            min_currents[i] = 0
    return min_currents, counts

# tested


def set_current_counterdiff(diff_current: float,
                            current: float,
                            load: Load,
                            surplus: bool = False) -> None:
    required_currents = load.data.control_parameter.required_currents
    if isinstance(load, Chargepoint):
        considered_current = consider_less_charging_chargepoint_in_loadmanagement(
            load, current)
    else:
        considered_current = current
    # gar nicht ladende Autos?
    diff = max(considered_current - diff_current, 0)
    diffs = [diff if required_currents[i] != 0 else 0 for i in range(3)]
    if max(diffs) > 0:
        counters = data.data.counter_all_data.get_counters_to_check(load.num)
        for counter in counters:
            if surplus:
                data.data.counter_data[counter].update_surplus_values_left(
                    diffs,
                    voltages_mean(load.data.get.voltages))
            else:
                data.data.counter_data[counter].update_values_left(
                    diffs,
                    voltages_mean(load.data.get.voltages))
        data.data.io_actions.dimming_set_import_power_left({"type": "cp" if isinstance(
            load, Chargepoint) else "consumer", "id": load.num}, sum(diffs)*230)

    load.data.set.current = current
    log.info(f"{'LP' if isinstance(load, Chargepoint) else 'Verbraucher'} {load.num}: Stromstärke {current}A")

# tested


def get_current_to_set(set_current: float, diff: float, prev_current: float) -> float:
    """Der neue Strom darf nicht höher als der in dieser Stufe bisher gesetzter sein, um das LM der untergeordneten
    Zähler nicht zu untergraben. Der Vergleich muss positiv sein, wenn zum ersten Mal auf dieser Stufe ein Strom gesetzt
    wird."""
    new_current = prev_current + diff
    if set_current is not None:
        if new_current > set_current:
            log.debug("Neuer Soll-Strom darf nicht höher als bisher gesetzter sein: "
                      f"bisher {set_current}A, neuer {new_current}")
            return set_current
    return new_current

# tested


def available_current_for_load(load: Load,
                               counts: List[int],
                               available_currents: List[float],
                               missing_currents: List[float]) -> float:
    control_parameter = load.data.control_parameter
    available_current = float("inf")
    missing_current_cp = control_parameter.required_current - load.data.set.target_current

    for i in range(0, 3):
        if isinstance(load, Chargepoint) and load.data.set.charging_ev_data.data.full_power:
            shared_with = 1
        else:
            shared_with = counts[i]
        if (control_parameter.required_currents[i] != 0 and missing_currents[i] != available_currents[i]):
            available_current = min(min(missing_current_cp, available_currents[i]/shared_with), available_current)

    if available_current == float("inf"):
        available_current = missing_current_cp
    return available_current


def update_raw_data(preferenced_loads: List[Load],
                    diff_to_zero: bool = False,
                    surplus: bool = False) -> None:
    """alle CP, die schon einen Soll-Strom haben, wieder herausrechnen, da dieser neu gesetzt wird
        und die neue Differenz bei den Zählern eingetragen wird."""
    for load in preferenced_loads:
        required_currents = load.data.control_parameter.required_currents
        max_target_set_current = max(load.data.set.target_current, load.data.set.current or 0)
        if isinstance(load, Chargepoint):
            max_target_set_current = consider_less_charging_chargepoint_in_loadmanagement(
                load, max_target_set_current)

        if diff_to_zero is False:
            if load.data.control_parameter.min_current < max_target_set_current:
                if surplus:
                    diffs = [load.data.set.target_current -
                             max_target_set_current if required_currents[i] != 0 else 0 for i in range(3)]
                else:
                    diffs = [load.data.control_parameter.min_current -
                             max_target_set_current if required_currents[i] != 0 else 0 for i in range(3)]
            else:
                continue
        else:
            if load.data.control_parameter.min_current <= max_target_set_current:
                diffs = [-load.data.control_parameter.min_current if required_currents[i]
                         != 0 else 0 for i in range(3)]
            else:
                continue
        counters = data.data.counter_all_data.get_counters_to_check(load.num)
        for counter in counters:
            if surplus:
                data.data.counter_data[counter].update_surplus_values_left(
                    diffs,
                    voltages_mean(load.data.get.voltages))
            else:
                data.data.counter_data[counter].update_values_left(diffs, voltages_mean(load.data.get.voltages))
        data.data.io_actions.dimming_set_import_power_left({"type": "cp" if isinstance(
            load, Chargepoint) else "consumer", "id": load.num}, sum(diffs)*230)


def consider_less_charging_chargepoint_in_loadmanagement(cp: Chargepoint, set_current: float) -> bool:
    if (data.data.counter_all_data.data.config.consider_less_charging is False and
        ((set_current -
          cp.data.set.charging_ev_data.ev_template.data.nominal_difference) > get_medium_charging_current(
              cp.data.get.currents) and
         cp.data.control_parameter.timestamp_charge_start is not None and
         check_timestamp(cp.data.control_parameter.timestamp_charge_start, LESS_CHARGING_TIMEOUT) is False)):
        log.debug(
            f"LP {cp.num} lädt deutlich unter dem Sollstrom und wird nur mit {cp.data.get.currents}A berücksichtigt.")
        return get_medium_charging_current(cp.data.get.currents)
    else:
        return set_current
# tested


def get_missing_currents_left(preferenced_loads: List[Load]) -> Tuple[List[float], List[int]]:
    missing_currents = [0.0]*3
    counts = [0]*3
    for load in preferenced_loads:
        required_currents = load.data.control_parameter.required_currents
        for i in range(0, 3):
            if required_currents[i] != 0:
                counts[i] += 1
                try:
                    missing_currents[i] += required_currents[i] - load.data.control_parameter.min_current
                except KeyError:
                    missing_currents[i] += max(required_currents) - load.data.control_parameter.min_current
            else:
                missing_currents[i] += 0
    return missing_currents, counts


def reset_current_to_target_current():
    """target_current enthält die gesetzte Stromstärke der vorherigen Stufe. Notwendig, um zB bei der
    Mindeststromstärke erkennen zu können, ob diese ein vom LM begrenzter Strom aus Stufe 2 oder der Mindeststrom
    aus Stufe 1 ist."""
    for load in (list(data.data.cp_data.values()) + list(data.data.consumer_data.values())):
        try:
            load.data.set.target_current = load.data.set.current
        except Exception:
            log.exception(f"Fehler im Algorithmus-Modul für "
                          f"{'Ladepunkt' if isinstance(load, Chargepoint) else 'Verbraucher'}{load.num}")
