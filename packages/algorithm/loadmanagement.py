""" Lastmangement

Das LM enthält ein Offset, das aktiv ist, wenn ein Ladepunkt eingeschaltet/hoch-/runtergeregelt werden soll, 
aber nicht, wenn geprüft wird, ob in der gesamten Anlage ein Zähler die Maximalwerte überschreitet.
So wird ein Schwingen vermieden, da die Ladepunkte auf Maximum-Offset geregelt werden, aber das Maximum geprüft wird.

Die L1 Phase des Ladepunkts muss nicht zwingend an die L1 Phase der EVU angeschlossen sein. Aktuell gibt es die Information,
welche LP-Phase an welche EVU-Phase angeschlossen ist, nicht. Beim einphasigen Laden wird deshalb auf allen 3 Phasen geprüft,
ob genug Leistung/Stromstärke verfügbar ist.
"""

from . import data
from ..helpermodules import log

overloaded_counters = {} # {counter: [max_overshoot, phase_with_max_overshoot]}
# phase_with_max_overshoot = -1 -> max. Lesistung wurde überschritten, es ist egal, auf welcher Phase reduziert wird.
# phase_with_max_overshoot = 0  -> Es ist nicht bekannt, auf welcher EVU/LP-Phase die Überlastung stattfindet, deshalb müssen alle Phasen reduziert werden.
# phase_with_max_overshoot = 1-3 -> Phase, auf der die Überlastung auftritt

def loadmanagement_for_cp(chargepoint, required_power, required_current, phases):
    """ prüft für den angegebenen Ladepunkt, ob im Zweig des Ladepunkts die maximale Stromstärke oder Bezug überschritten wird.

    Parameter
    ---------
    chargepoint: class
        Ladepunkt
    required_power: float
        Leistung, mit der geladen werden soll
    required_current: list
        Stromstärke, mit der geladen werden soll
    phases: int
        Phasen, mit denen geladen werden soll
    Return
    ------
    bool: Lastmanagement aktiv?
    """
    loadmanagement = False
    loadmanagement_all_conditions = False
    global overloaded_counters
    overloaded_counters.clear()
    try:
        # Wenn dreiphasig geladen werden soll, ist es egal, auf welcher Phase L1 angeschlossen ist.
        if phases == 3:
            required_current_phases = [required_current]*3
        else:
            # Es ist nicht bekannt, an welcher Phase der EVU L1 des LP angeschlosssen ist.
            if chargepoint.data["config"]["phase_1"] == 0:
                # Es muss noch auf allen 3 Phasen genügend Reserve sein.
                 required_current_phases = [required_current]*3
            elif chargepoint.data["config"]["phase_1"] == 1:
                required_current_phases = [required_current, 0, 0]
            elif chargepoint.data["config"]["phase_1"] == 2:
                required_current_phases= [0, required_current, 0]
            elif chargepoint.data["config"]["phase_1"] == 3:
                required_current_phases = [0, 0, required_current]
        counters = data.data.counter_data["all"].get_counters_to_check(chargepoint)
        # Stromstärke merken, wenn das Lastmanagement nicht aktiv wird, wird nach der Prüfung die neue verwendete Stromstärke gesetzt.
        for counter in counters[:-1]:
            try:
                loadmanagement, overshoot, phase = _check_max_current(counter, required_current_phases, phases, True)
                if loadmanagement == True:
                    loadmanagement_all_conditions = True
                    overloaded_counters[counter] = [overshoot, phase]
            except Exception as e:
                log.exception_logging(e)
        # Wenn das Lastamanagement bei den Zwischenzählern aktiv wurde, darf es nicht wieder zurück gesetzt werden.
        loadmanagement= _loadmanagement_for_evu(required_power, required_current_phases, phases, True)
        if loadmanagement == True:
            loadmanagement_all_conditions = True
        
        data.data.counter_data["all"].data["set"]["loadmanagement"] = loadmanagement_all_conditions
        return loadmanagement_all_conditions, overloaded_counters
    except Exception as e:
        log.exception_logging(e)
        return False, None

def loadmanagement_for_counters():
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
        loadmanagement_all_conditions = _loadmanagement_for_evu(0 , [0, 0, 0], 3, False)
        # Überprüfung der Zwischenzähler
        loadmanagement = _check_all_intermediate_counters(data.data.counter_data["all"].data["get"]["hierarchy"][0])
        # Wenn das Lastmanagement aktiv war, darf es nicht wieder zurück gesetzt werden.
        if loadmanagement_all_conditions == False:
            loadmanagement_all_conditions = loadmanagement
        data.data.counter_data["all"].data["set"]["loadmanagement"] = loadmanagement_all_conditions
        return loadmanagement_all_conditions, overloaded_counters
    except Exception as e:
        log.exception_logging(e)
        return False, None



def get_overloaded_counters():
    return overloaded_counters



def _check_all_intermediate_counters(child):
    """ Rekursive Funktion, die für alle Zwischenzähler prüft, ob die Maximal-Stromstärke ohne Beachtung des Offsets eingehalten wird.

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
            if "counter" in child["id"]:
                # Wenn Objekt ein Zähler ist, Stromstärke prüfen.
                loadmanagement, overshoot, phase = _check_max_current(child["id"], [0, 0, 0], 3, False)
                if loadmanagement == True:
                    overloaded_counters[child["id"]] = [overshoot, phase]
                    return True
            # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
            if len(child["children"]) != 0:
                loadmanagement = _check_all_intermediate_counters(child)
                if loadmanagement == True:
                    return True
        except Exception as e:
            log.exception_logging(e)
    # Wenn alle durchgegangen wurden und das Lastamangement nicht aktiv geworden ist.
    else:
        return False

# Überprüfen der Werte

def _loadmanagement_for_evu(required_power, required_current_phases, phases, offset):
    """ führt die Überprüfung für das Lastmanagement der EVU durch und prüft dabei die maximale Stromstärke, maximalen Bezug und maximale Schieflast, falls aktiv.

    Parameter
    ---------
    required_power: float
        Leistung, mit der geladen werden soll
    required_current_phases: list
        Stromstärke, mit der geladen werden soll
    phases: int
        Phasen, mit denen geladen werden soll
    offset: bool
        Beachtung des Offsets
    Return
    ------
    loadmanagement: bool
        Lastmanagement aktiv/inaktiv, verbleibende verfügbare Leistung, genutzter Strom
    """
    max_current_overshoot = 0
    max_overshoot_phase = 0
    consumption_left = 0
    global overloaded_counters
    try:
        # Wenn das Lastmanagement einmal aktiv gesetzt wurde, darf es nicht mehr zurück gesetzt werden.
        loadmanagement_all_conditions = False
        loadmanagement, consumption_left = _check_max_power(required_power, offset)
        if loadmanagement == True:
            loadmanagement_all_conditions = True
            if consumption_left >= 0:
                overshoot = consumption_left /230 / 3
            else:
                overshoot = (consumption_left*-1) /230 / 3
            if max_current_overshoot < overshoot:
                max_current_overshoot = overshoot
                max_overshoot_phase = -1
        loadmanagement, overshoot, phase = _check_max_current("counter0", required_current_phases, phases, offset)
        if loadmanagement == True:
            loadmanagement_all_conditions = True
            # Wenn max_overshoot_phase -1 ist, wurde die maximale Gesamtleistung überschrittten und max_current_overshoot muss, 
            # wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert werden.
            if max_overshoot_phase == -1:
                overshoot_one_phase = max_current_overshoot * (3 - phases +1)
            else:
                overshoot_one_phase = max_current_overshoot
            if overshoot_one_phase < overshoot:
                max_current_overshoot = overshoot
                max_overshoot_phase = phase
        loadmanagement, overshoot, phase = _check_unbalanced_load(data.data.counter_data["counter0"].data["set"]["current_used"], offset)
        if loadmanagement == True:
            loadmanagement_all_conditions = True
            # Wenn max_overshoot_phase -1 ist, wurde die maximale Gesamtleistung überschrittten und max_current_overshoot muss, 
            # wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert werden.
            if max_overshoot_phase == -1:
                overshoot_one_phase = max_current_overshoot * (3 - phases +1)
            else:
                overshoot_one_phase = max_current_overshoot
            if overshoot_one_phase < overshoot:
                max_current_overshoot = overshoot
                max_overshoot_phase = phase
        if loadmanagement_all_conditions == True:
            overloaded_counters["counter0"] = [max_current_overshoot, max_overshoot_phase]
        return loadmanagement_all_conditions
    except Exception as e:
        log.exception_logging(e)
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
        Lastmanagement aktiv/inaktiv, verbleibende verfügbare Leistung inkl Offset (da beim Anpassen des Ladestroms nie  der Maximalbezug ausgereizt werden)
    """
    if offset == True:
        offset_power = 300
    else:
        offset_power = 0
    try:
        consumption_left = data.data.counter_data["counter0"].data["set"]["consumption_left"] - required_power - offset_power
        data.data.counter_data["counter0"].data["set"]["consumption_left"] -= required_power
        # Float-Ungenauigkeiten abfangen
        if consumption_left >= -0.01:
            return False, data.data.counter_data["counter0"].data["set"]["consumption_left"] - 300
        else:
            return True, data.data.counter_data["counter0"].data["set"]["consumption_left"] - 300
    except Exception as e:
        log.exception_logging(e)
        return 0, False

def _check_max_current(counter, required_current_phases, phases, offset):
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
    current_used = [0, 0, 0]
    loadmanagement = False
    max_current_overshoot = 0
    if offset == True:
        offset_current = 300 / 230 / phases
    else:
        offset_current = 0
    try:
        for phase in range(3):
            current_used[phase] = data.data.counter_data[counter].data["set"]["current_used"][phase] + required_current_phases[phase]
            # Wird die maximal zulässige Stromstärke inklusive des Offsets eingehlaten?
            if current_used[phase] < data.data.counter_data[counter].data["config"]["max_current"][phase] - offset_current:
                loadmanagement = False
            else:
                if (current_used[phase]-(data.data.counter_data[counter].data["config"]["max_current"][phase] - offset_current)) > max_current_overshoot:
                    max_current_overshoot = current_used[phase]-data.data.counter_data[counter].data["config"]["max_current"][phase]
        if max_current_overshoot != 0:
            loadmanagement = True
            if offset == True:
                log.message_debug_log("warning", "Benoetigte Stromstaerke "+str(required_current_phases[phase])+" ueberschreitet unter Beachtung des Offsets die zulaessige Stromstaerke an Phase "+str(phase)+ " um "+str(max_current_overshoot)+"A.")
            else:
                log.message_debug_log("warning", "Benoetigte Stromstaerke "+str(required_current_phases[phase])+" ueberschreitet ohne Beachtung des Offsets die zulaessige Stromstaerke an Phase "+str(phase)+ " um "+str(max_current_overshoot)+"A.")
        data.data.counter_data[counter].data["set"]["current_used"] = current_used
        # Wenn Zähler geprüft werden, wird ohne Offset geprüft. Beim Runterregeln soll aber das Offset berücksichtigt werden, um Schwingen zu vermeiden.
        return loadmanagement, max_current_overshoot + (300 / 230 / phases), current_used.index(max(current_used))
    except Exception as e:
        log.exception_logging(e)
        return False, 0, 0

def _check_unbalanced_load(current_used, offset):
    """ prüft, ob die Schieflastbegrenzug aktiv ist und ob diese eingehalten wird.

    Parameter
    ---------
    current_used: list
        Strom, der gebraucht wird
    offset: bool
        Beachtung des Offsets
    Return
    ------
    bool: Lastmanagement aktiv/inaktiv
    max_current_overshoot: maximale Überschreitung der Stromstärke
    int: Phase, die den höchsten Strom verbraucht
    """
    if data.data.general_data["general"].data["chargemode_config"]["unbalanced_load"] == True:
        max_current_overshoot = 0
        if offset == True:
            offset_current = 1
        else:
            offset_current = 0
        try:
            min_current = min(current_used)
            if min_current < 0:
                min_current = 0
            max_current = max(current_used)
            if max_current < 0:
                max_current = 0
            if (max_current - min_current) <= data.data.general_data["general"].data["chargemode_config"]["unbalanced_load_limit"] - offset_current:
                return False, None, 0
            else:
                max_current_overshoot = (max_current - min_current) - data.data.general_data["general"].data["chargemode_config"]["unbalanced_load_limit"]
                log.message_debug_log("warning", "Schieflast wurde ueberschritten.")
                return True, max_current_overshoot + 1, current_used.index(max_current)+1
        except Exception as e:
            log.exception_logging(e)
            return False, 0, 0
    else:
        return False, None, 0
