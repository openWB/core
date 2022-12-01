""" Lastmanagement

Das LM enthält ein Offset, das aktiv ist, wenn ein Ladepunkt eingeschaltet/hoch-/runtergeregelt werden soll,
aber nicht, wenn geprüft wird, ob in der gesamten Anlage ein Zähler die Maximalwerte überschreitet.
So wird ein Schwingen vermieden, da die Ladepunkte auf Maximum-Offset geregelt werden, aber das Maximum geprüft wird.

Die L1 Phase des Ladepunkts muss nicht zwingend an die L1 Phase der EVU angeschlossen sein. Aktuell gibt es die
Information, welche LP-Phase an welche EVU-Phase angeschlossen ist, nicht. Beim einphasigen Laden wird deshalb
auf allen 3 Phasen geprüft, ob genug Leistung/Stromstärke verfügbar ist.
"""
import logging
from typing import Dict, List, Tuple

from control import data
from control.chargepoint import Chargepoint
from helpermodules.phase_mapping import convert_single_evu_phase_to_cp_phase
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)

# {counter: [max_overshoot, phase_with_max_overshoot]}
overloaded_counters = {}
# phase_with_max_overshoot = -1 -> max. Leistung wurde überschritten, es ist egal, auf welcher Phase reduziert wird.
# phase_with_max_overshoot = 0  -> Es ist nicht bekannt, auf welcher EVU/LP-Phase die Überlastung stattfindet, deshalb
#                                  müssen alle Phasen reduziert werden.
# phase_with_max_overshoot = 1-3 -> Phase, auf der die Überlastung auftritt


def loadmanagement_for_cp(chargepoint: Chargepoint,
                          required_current: float,
                          phases: int) -> Tuple[bool, Dict[str, Tuple[float, int]]]:
    """ prüft für den angegebenen Ladepunkt, ob im Zweig des Ladepunkts die maximale Stromstärke oder Bezug
    überschritten wird.
    """
    loadmanagement = False
    loadmanagement_all_conditions = False
    global overloaded_counters
    overloaded_counters.clear()
    try:
        required_current_phases = [0.0]*3
        try:
            for i in range(0, phases):
                evu_phase = convert_single_evu_phase_to_cp_phase(chargepoint.data.config.phase_1, i)
                required_current_phases[evu_phase] = required_current
        except KeyError:
            required_current_phases = [required_current]*3
        counters = data.data.counter_all_data.get_counters_to_check(
            chargepoint.num)
        # Stromstärke merken, wenn das Lastmanagement nicht aktiv wird, wird nach der Prüfung die neue verwendete
        # Stromstärke gesetzt.
        for counter in counters[:-1]:
            try:
                loadmanagement, overshoot, phase = _check_max_currents(
                    counter, required_current_phases, phases, True)
                if loadmanagement:
                    loadmanagement_all_conditions = True
                    overloaded_counters[counter] = [overshoot, phase]
            except Exception:
                log.exception("Fehler im Lastmanagement-Modul "+str(counter))
        # Wenn das Lastmanagement bei den Zwischenzählern aktiv wurde, darf es nicht wieder zurück gesetzt werden.
        loadmanagement = _loadmanagement_for_evu(
            required_current_phases, phases, True)
        if loadmanagement:
            loadmanagement_all_conditions = True

        data.data.counter_all_data.data.set.loadmanagement_active = loadmanagement_all_conditions
        return loadmanagement_all_conditions, overloaded_counters
    except Exception:
        log.exception("Fehler im Lastmanagement-Modul")
        return False, {}


def loadmanagement_for_counters() -> Tuple[bool, Dict[str, Tuple[float, int]]]:
    """ überprüft bei allen Zählern, ob die Maximal-Werte eingehalten werden.

    Return
    ------
    True/False: Lastmanagement aktiv/inaktiv
    """
    global overloaded_counters
    overloaded_counters.clear()
    loadmanagement_all_conditions = False
    try:
        # Für den EVU-Zähler max. Leistung, max. Stromstärke und Schieflast überprüfen.
        loadmanagement_all_conditions = _loadmanagement_for_evu(
            [0, 0, 0], 3, False)
        # Überprüfung der Zwischenzähler
        loadmanagement = _check_all_intermediate_counters(
            data.data.counter_all_data.data.get.hierarchy[0])
        # Wenn das Lastmanagement aktiv war, darf es nicht wieder zurück gesetzt werden.
        if not loadmanagement_all_conditions:
            loadmanagement_all_conditions = loadmanagement
        data.data.counter_all_data.data.set.loadmanagement_active = loadmanagement_all_conditions
        return loadmanagement_all_conditions, overloaded_counters
    except Exception:
        log.exception("Fehler im Lastmanagement-Modul")
        return False, {}


def get_overloaded_counters():
    return overloaded_counters


def _check_all_intermediate_counters(child):
    """ Rekursive Funktion, die für alle Zwischenzähler prüft, ob die Maximal-Stromstärke ohne Beachtung des Offsets
    eingehalten wird.

    Parameter
    ---------
    child: Zweig, der als nächstes durchsucht werden soll
    Return
    ------
    True/False: Lastmanagement aktiv/inaktiv
    """
    global overloaded_counters
    # Alle Objekte der Ebene durchgehen
    for child in child["children"]:
        try:
            if child["type"] == ComponentType.COUNTER.value:
                # Wenn Objekt ein Zähler ist, Stromstärke prüfen.
                loadmanagement, overshoot, phase = _check_max_currents(
                    f"counter{child['id']}", [0, 0, 0], 3, False)
                if loadmanagement:
                    overloaded_counters[f"counter{child['id']}"] = [overshoot, phase]
                    return True
            # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
            if len(child["children"]) != 0:
                loadmanagement = _check_all_intermediate_counters(child)
                if loadmanagement:
                    return True
        except Exception:
            log.exception("Fehler im Lastmanagement-Modul für Zähler "+str(child))
    # Wenn alle durchgegangen wurden und das Lastmanagement nicht aktiv geworden ist.
    else:
        return False

# Überprüfen der Werte


def _loadmanagement_for_evu(required_current_phases: List[float], phases: int, offset: bool) -> bool:
    """ führt die Überprüfung für das Lastmanagement der EVU durch und prüft dabei die maximale Stromstärke, maximalen
    Bezug und maximale Schieflast, falls aktiv.
    """
    evu_counter = data.data.counter_all_data.get_evu_counter_str()
    max_current_overshoot = 0
    max_overshoot_phase = 0
    consumption_left = 0
    global overloaded_counters
    try:
        # Wenn das Lastmanagement einmal aktiv gesetzt wurde, darf es nicht mehr zurück gesetzt werden.
        loadmanagement_all_conditions = False
        loadmanagement, consumption_left = _check_max_power(
            sum(required_current_phases) * 230, offset)
        if loadmanagement:
            loadmanagement_all_conditions = True
            if consumption_left >= 0:
                overshoot = consumption_left / 230 / 3
            else:
                overshoot = (consumption_left*-1) / 230 / 3
            if max_current_overshoot < overshoot:
                max_current_overshoot = overshoot
                max_overshoot_phase = -1
        loadmanagement, overshoot_one_phase, phase = _check_max_currents(
            evu_counter, required_current_phases, phases, offset)
        if loadmanagement:
            loadmanagement_all_conditions = True
            # Wenn phase -1 ist, wurde die maximale Gesamtleistung überschritten und
            # overshoot_one_phase muss, wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert werden.
            if phase == -1:
                overshoot_one_phase = overshoot_one_phase * (3 - phases + 1)
            if max_current_overshoot < overshoot_one_phase:
                max_current_overshoot = overshoot_one_phase
                max_overshoot_phase = phase
        loadmanagement, overshoot_one_phase, phase = _check_unbalanced_load(
            data.data.counter_data[evu_counter].data["set"].get("currents_used"), offset)
        if loadmanagement:
            loadmanagement_all_conditions = True
            # Wenn phase -1 ist, wurde die maximale Gesamtleistung überschritten und
            # overshoot_one_phase muss, wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert werden.
            if phase == -1:
                overshoot_one_phase = overshoot_one_phase * (3 - phases + 1)
            if max_current_overshoot < overshoot_one_phase:
                max_current_overshoot = overshoot_one_phase
                max_overshoot_phase = phase
        if loadmanagement_all_conditions:
            overloaded_counters[evu_counter] = [
                max_current_overshoot, max_overshoot_phase]
        return loadmanagement_all_conditions
    except Exception:
        log.exception("Fehler im Lastmanagement-Modul")
        return False


def _check_max_power(required_power, offset):
    """ prüft, dass die maximale Leistung nicht überschritten wird.

    Parameter
    ---------
    required_power: int
        benötigte Leistung
    offset: bool
        Beachtung des Offsets
    Return
    ------
    loadmanagement, consumption_left: bool, int
        Lastmanagement aktiv/inaktiv, verbleibende verfügbare Leistung inklusive Offset (da beim Anpassen des
        Ladestroms nie der Maximalbezug ausgereizt werden)
    """
    evu_counter = data.data.counter_all_data.get_evu_counter_str()
    if offset:
        offset_power = 300
    else:
        offset_power = 0
    try:
        consumption_left = data.data.counter_data[evu_counter].data[
            "set"]["consumption_left"] - required_power - offset_power
        data.data.counter_data[evu_counter].data["set"]["consumption_left"] -= required_power
        # Float-Ungenauigkeiten abfangen
        if consumption_left >= -0.01:
            return False, data.data.counter_data[evu_counter].data["set"]["consumption_left"] - 300
        else:
            return True, data.data.counter_data[evu_counter].data["set"]["consumption_left"] - 300
    except Exception:
        log.exception("Fehler im Lastmanagement-Modul")
        return 0, False


def _check_max_currents(counter, required_current_phases, phases, offset):
    """ prüft, ob die maximale Stromstärke aller Phasen eingehalten wird.

    Parameter
    ---------
    counter: str
        Zähler, der geprüft werden soll
    required_current_phases: list
        Stromstärke, mit der geladen werden soll
    phases: int
        Phasen, mit denen geladen werden soll
    offset: bool
        Beachtung des Offsets
    Return
    ------
    loadmanagement: bool
        Lastmanagement aktiv/inaktiv
    max_current_overshoot: float
        maximale Überschreitung des zulässigen Stroms
    phase: int
        Phase, die den höchsten Strom verbraucht
    """
    if data.data.counter_data[counter].data["set"].get("currents_used"):
        currents_used = [0, 0, 0]
        max_current_overshoot = 0
        if offset:
            offset_current = 2
        else:
            offset_current = 0
        try:
            loadmanagement = False
            for phase in range(3):
                currents_used[phase] = data.data.counter_data[counter].data["set"]["currents_used"][phase] + \
                    required_current_phases[phase]
                # Wird die maximal zulässige Stromstärke inklusive des Offsets eingehalten?
                max_current_of_phase = data.data.counter_data[counter].data["config"]["max_currents"][phase]
                if (currents_used[phase] > max_current_of_phase - offset_current):
                    if ((currents_used[phase]-(max_current_of_phase - offset_current)) > max_current_overshoot):
                        max_current_overshoot = currents_used[phase] - max_current_of_phase
                    loadmanagement = True
            if max_current_overshoot > 0:
                if offset:
                    log.debug("Strom "+str(currents_used))
                    log.warning(
                        f"Benötigte Stromstärke {required_current_phases} überschreitet unter Beachtung des Offsets"
                        f" die zulässige Stromstärke an Phase {(currents_used.index(max(currents_used))+1)} um"
                        f" {max_current_overshoot}A.")
                else:
                    log.debug("Strom "+str(currents_used))
                    log.warning(
                        f"Benötigte Stromstärke {required_current_phases} überschreitet ohne Beachtung des Offsets"
                        f" die zulässige Stromstärke an Phase {(currents_used.index(max(currents_used))+1)} um"
                        f" {max_current_overshoot}A.")
            data.data.counter_data[counter].data["set"]["currents_used"] = currents_used
            # Wenn Zähler geprüft werden, wird ohne Offset geprüft. Beim Runterregeln soll aber das Offset
            # berücksichtigt werden, um Schwingen zu vermeiden.
            return (loadmanagement,
                    max_current_overshoot + 2,
                    currents_used.index(max(currents_used))+1)
        except Exception:
            log.exception("Fehler im Lastmanagement-Modul")
            return False, 0, 0
    else:
        return False, 0, 0


def _check_unbalanced_load(currents_used, offset) -> Tuple[bool, float, float]:
    """ prüft, ob die Schieflastbegrenzung aktiv ist und ob diese eingehalten wird.

    Parameter
    ---------
    currents_used: list
        Strom, der gebraucht wird
    offset: bool
        Beachtung des Offsets
    Return
    ------
    bool: Lastmanagement aktiv/inaktiv
    max_current_overshoot: maximale Überschreitung der Stromstärke
    int: Phase, die den höchsten Strom verbraucht
    """
    if data.data.general_data.data.chargemode_config.unbalanced_load and currents_used:
        max_current_overshoot = 0
        if offset:
            offset_current = 1
        else:
            offset_current = 0
        try:
            min_current = min(currents_used)
            if min_current < 0:
                min_current = 0
            max_current = max(currents_used)
            if max_current < 0:
                max_current = 0
            if ((max_current - min_current) <=
                    data.data.general_data.data.chargemode_config.unbalanced_load_limit - offset_current):
                return False, 0, 0
            else:
                max_current_overshoot = (
                    max_current - min_current) - \
                    data.data.general_data.data.chargemode_config.unbalanced_load_limit
                log.warning("Schieflast wurde überschritten.")
                return True, max_current_overshoot + 1, currents_used.index(max_current)+1
        except Exception:
            log.exception("Fehler im Lastmanagement-Modul")
            return False, 0, 0
    else:
        return False, 0, 0


def sort_overloaded_counter(overloaded_counters: Dict[str, Tuple[float, int]]) -> List[Tuple[str, Tuple[float, int]]]:
    return sorted(overloaded_counters.items(), key=lambda e: e[1][0], reverse=True)
