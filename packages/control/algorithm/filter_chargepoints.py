# tested
import logging
from typing import List, Optional, Tuple

from control import data
from control.algorithm import common
from control.chargepoint import Chargepoint
from helpermodules.timecheck import convert_to_unix_timestamp

log = logging.getLogger(__name__)


def get_chargepoints_by_mode_and_counter(mode_tuple: Tuple[Optional[str], str, bool],
                                         counter: str) -> List[Chargepoint]:
    cps_to_counter = data.data.counter_all_data.get_chargepoints_of_counter(counter)
    cps_to_counter_ids = [int(cp[2:]) for cp in cps_to_counter]
    cps_by_mode = get_chargepoints_by_mode(mode_tuple)
    return list(filter(lambda cp: cp.num in cps_to_counter_ids, cps_by_mode))

# tested


def get_chargepoints_by_mode(mode_tuple: Tuple[Optional[str], str, bool]) -> List[Chargepoint]:
    mode = mode_tuple[0]
    submode = mode_tuple[1]
    prio = mode_tuple[2]
    # enthält alle LP, auf die das Tupel zutrifft
    valid_chargepoints = []
    for cp in data.data.cp_data.values():
        if cp.data.set.charging_ev != -1:
            charging_ev = cp.data.set.charging_ev_data
            if ((charging_ev.data.control_parameter.prio == prio) and
                (charging_ev.data.control_parameter.chargemode == mode or
                    mode is None) and
                    (charging_ev.data.control_parameter.submode == submode)):
                valid_chargepoints.append(cp)
    return valid_chargepoints


def get_preferenced_chargepoint_charging(
        chargepoints: List[Chargepoint]) -> Tuple[List[Chargepoint], List[Chargepoint]]:
    preferenced_chargepoints = _get_preferenced_chargepoint(chargepoints)
    preferenced_chargepoints_with_set_current = []
    preferenced_chargepoints_without_set_current = []
    for cp in preferenced_chargepoints:
        if cp.data.set.target_current == 0:
            log.debug(
                f"LP {cp.num}: Keine Zuteilung des Mindeststroms, daher keine weitere Berücksichtigung")
            preferenced_chargepoints_without_set_current.append(cp)
        elif max(cp.data.get.currents) == 0:
            log.debug(
                f"LP {cp.num}: Lädt nicht, daher keine weitere Berücksichtigung")
            preferenced_chargepoints_without_set_current.append(cp)
        else:
            preferenced_chargepoints_with_set_current.append(cp)
    return preferenced_chargepoints_with_set_current, preferenced_chargepoints_without_set_current


def get_chargepoints_pv_charging() -> List[Chargepoint]:
    chargepoints: List[Chargepoint] = []
    for mode in common.CHARGEMODES[8: 12]:
        chargepoints.extend(get_chargepoints_by_mode(mode))
    return chargepoints


def get_chargepoints_surplus_controlled() -> List[Chargepoint]:
    chargepoints: List[Chargepoint] = []
    for mode in common.CHARGEMODES[6: 12]:
        chargepoints.extend(get_chargepoints_by_mode(mode))
    return chargepoints

# tested


def _get_preferenced_chargepoint(valid_chargepoints: List[Chargepoint]) -> List:
    """ermittelt die Ladepunkte in der Reihenfolge, in der sie geladen/gestoppt werden sollen. Die Bedingungen
    sind:
    geringste Mindeststromstärke, niedrigster SoC, frühester Ansteck-Zeitpunkt(Einschalten)/Lademenge(Abschalten),
    niedrigste Ladepunktnummer.
    """
    preferenced_chargepoints = []
    chargepoints = dict.fromkeys(valid_chargepoints)
    try:
        # Bedingungen in der Reihenfolge, in der sie geprüft werden.
        condition_types = ("min_current", "soc", "imported_since_plugged", "plug_in", "num")
        # Bedingung, die geprüft wird (entspricht Index von condition_types)
        condition = 0
        if chargepoints:
            while len(chargepoints) > 0:
                # entsprechend der Bedingung die Values im Dictionary füllen
                if condition_types[condition] == "min_current":
                    chargepoints.update(
                        (cp, cp.data.set.charging_ev_data.data.control_parameter.required_current)
                        for cp in chargepoints.keys())
                elif condition_types[condition] == "soc":
                    chargepoints.update(
                        (cp, cp.data.set.charging_ev_data.data.get.soc) for cp in chargepoints.keys())
                elif condition_types[condition] == "plug_in":
                    chargepoints.update((cp, convert_to_unix_timestamp(cp.data.set.plug_time))
                                        for cp in chargepoints.keys())
                elif condition_types[condition] == "imported_since_plugged":
                    chargepoints.update((cp, cp.data.set.log.imported_since_plugged) for cp in chargepoints.keys())
                else:
                    chargepoints.update((cp, cp.num) for cp in chargepoints.keys())

                # kleinsten Value im Dictionary ermitteln
                extreme_value = min(chargepoints.values())
                # dazugehörige Keys ermitteln
                extreme_cp = [
                    key for key in chargepoints if chargepoints[key] == extreme_value]
                if len(extreme_cp) > 1:
                    # Wenn es mehrere LP gibt, die den gleichen Minimalwert haben, nächste Bedingung prüfen.
                    condition += 1
                else:
                    preferenced_chargepoints.append(extreme_cp[0])
                    chargepoints.pop(extreme_cp[0])
        if preferenced_chargepoints:
            log.debug(f"Geordnete Ladepunkte {[cp.num for cp in preferenced_chargepoints]}")
        return preferenced_chargepoints
    except Exception:
        log.exception("Fehler im Algorithmus-Modul")
        return preferenced_chargepoints
