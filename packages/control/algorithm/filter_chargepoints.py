# tested
import logging
from typing import List, Optional, Tuple

from control import data
from control.chargepoint.chargepoint import Chargepoint

log = logging.getLogger(__name__)


def get_chargepoints_by_mode_and_counter_and_lm_prio(chargemodes: Tuple[Tuple[Optional[str], str]],
                                                     counter: str,
                                                     prio_group: List[Chargepoint]) -> List[Chargepoint]:
    cps_to_counter = data.data.counter_all_data.get_chargepoints_of_counter(counter)
    cps_to_counter_ids = [int(cp[2:]) for cp in cps_to_counter]
    cps_by_mode = get_chargepoints_by_mode(chargemodes)
    return [
        cp for cp in prio_group
        if cp in cps_by_mode and cp.num in cps_to_counter_ids
    ]

# tested


def get_chargepoints_by_mode(chargemodes: Tuple[Tuple[Optional[str], str]]) -> List[Chargepoint]:
    cps = []
    for chargemode in chargemodes:
        for cp in data.data.cp_data.values():
            if (cp.data.control_parameter.required_current != 0 and
                (cp.data.control_parameter.chargemode == chargemode[0] or chargemode[0] is None) and
                    (cp.data.control_parameter.submode == chargemode[1])):
                cps.append(cp)
    return cps


def get_chargepoints_by_mode_and_lm_prio(chargemodes: Tuple[Tuple[Optional[str], str]],
                                         prio_group: List[Chargepoint]) -> List[Chargepoint]:
    cps_by_mode = get_chargepoints_by_mode(chargemodes)
    return [cp for cp in prio_group if cp in cps_by_mode]


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
                        (cp, cp.data.control_parameter.required_current)
                        for cp in chargepoints.keys())
                elif condition_types[condition] == "soc":
                    chargepoints.update(
                        (cp, cp.data.set.charging_ev_data.data.get.soc or 0) for cp in chargepoints.keys())
                elif condition_types[condition] == "plug_in":
                    chargepoints.update((cp, cp.data.set.plug_time)
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
