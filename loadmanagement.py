""" Lastmangement
"""

import data
import log

max_current_overshoot = 0
max_overshoot_counter = None
max_overshoot_phase = None

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
    current_used = {}
    consumption_left = 0
    global max_current_overshoot
    global max_overshoot_counter
    global max_overshoot_phase
    max_current_overshoot = 0
    max_overshoot_counter = None
    max_overshoot_phase = None
    loadmanagement_all_conditions = False
    try:
        counters = _get_counters_to_check(chargepoint)
        # Stromstärke merken, wenn das Lastmanagement nicht aktiv wird, wird nach der Prüfung die neue verwendete Stromstärke gesetzt.
        for counter in counters[:-1]:
            loadmanagement, current_used, overshoot, phase = _check_max_current(counter, required_current, phases)
            if loadmanagement == False:
                current_used[counter] = current_used
            else:
                loadmanagement_all_conditions = True
                if max_current_overshoot < overshoot:
                    max_current_overshoot = overshoot
                    max_overshoot_counter = counter
                    max_overshoot_phase = phase
        # Wenn das Lastamanagement bei den Zwischenzählern aktiv wurde, darf es nicht wieder zurück gesetzt werden.
        loadmanagement, consumption_left, current_used = _loadmanagement_for_evu(current_used, required_power, required_current, phases)
        if loadmanagement_all_conditions == False:
            loadmanagement_all_conditions = loadmanagement

        # Werte bei erfolgreichem Lastamanagement schreiben
        if loadmanagement_all_conditions == False:
            data.counter_data["counter0"].data["set"]["consumption_left"] = consumption_left
            log.message_debug_log("debug", str(data.counter_data["counter0"].data["set"]["consumption_left"])+"W EVU-Bezugs-Leistung, die fuer die folgenden Durchlaufe uebrig ist.")
            for counter in current_used:
                data.counter_data[counter].data["set"]["current_used"] = current_used[counter]
        data.counter_data["all"].data["set"]["loadmanagement"] = loadmanagement_all_conditions
        return data.counter_data["all"].data["set"]["loadmanagement"]
    except Exception as e:
        log.exception_logging(e)

def loadmanagement_for_counters():
    """ überprüft bei allen Zählern, ob die Maximal-Werte eingehalten werden.

    Return
    ------
    True/False: Lastmanagement aktiv/inaktiv
    """
    global max_current_overshoot
    global max_overshoot_counter
    global max_overshoot_phase
    max_current_overshoot = 0
    max_overshoot_counter = None
    max_overshoot_phase = None
    loadmanagement_all_conditions = False
    try:
        # Für den EVU-Zähler max. Leistung, max. Stromstärke und Schieflast überprüfen.
        loadmanagement_all_conditions = _loadmanagement_for_evu({}, 0 ,0, 3)[0]
        # Überprüfung der Zwischenzähler
        loadmanagement = _check_all_intermediate_counters(data.counter_data["all"].data["get"]["hierarchy"][0])
        # Wenn das Lastmanagement aktiv war, darf es nicht wieder zurück gesetzt werden.
        if loadmanagement_all_conditions == False:
            loadmanagement_all_conditions = loadmanagement
        data.counter_data["all"].data["set"]["loadmanagement"] = loadmanagement_all_conditions
        return loadmanagement
    except Exception as e:
        log.exception_logging(e)

def perform_loadmanagement():
    """ gibt den Zähler mit der gröpten Überlastung und die Überlastung sowie eine Liste der Ladepunkte, die in den folgenden Zweigen des Zählers sind, zurück.

    Return
    ------
    chargepoints: list
        Ladepunkte, die in den folgenden Zweigen des Zählers sind
    max_current_overshoot: float
        Größte Überlastung
    max_overshoot_phase: int
        Phase, in der die größte Überlastung auftritt
    """
    global max_current_overshoot
    global max_overshoot_counter
    global max_overshoot_phase
    global chargepoints
    chargepoints.clear()
    if max_current_overshoot != 0 and max_overshoot_counter != None and data.counter_data["all"].data["set"]["loadmanagement"] == True:
        if max_overshoot_counter == "counter0":
            counter_object = data.counter_data["all"].data["get"]["hierarchy"][0]
        else:
            counter_object = _look_for_object(data.counter_data["all"].data["get"]["hierarchy"][0], "counter", max_overshoot_counter[7:])
        _get_all_cp_connected_to_counter(counter_object)
        return chargepoints, max_current_overshoot, max_overshoot_phase
    else:
        log.message_debug_log("error", "Lastmanagement soll durchgefuehrt werden, obwohl keine Zaehler die Werte ueberschreiten.")

# Verarbeiten der Liste aus Zählern und Ladepunkten
counters = []
chargepoints = []

def _check_all_intermediate_counters(child):
    """ Rekursive Funktion, die für alle Zwischenzähler prüft, ob die Maximal-Stromstärke eingehalten wird.

    Parameter
    ---------
    child: Zweig, der als nächstes durchsucht werden soll
    Return
    ------
    True/False: Lastmanagement aktiv/inaktiv
    """
    global max_current_overshoot
    global max_overshoot_counter
    global max_overshoot_phase
    try:
        # Alle Objekte der Ebene durchgehen
        for child in child["children"]:
            if "counter" in child["id"]:
                # Wenn Objekt ein Zähler ist, Stromstärke prüfen.
                loadmanagement, _, overshoot, phase = _check_max_current(child["id"], 0, 3)
                if loadmanagement == True:
                    if max_current_overshoot < overshoot:
                        max_current_overshoot = overshoot
                        max_overshoot_counter = child["id"]
                        max_overshoot_phase = phase
                    return True
            # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
            if len(child["children"]) != 0:
                loadmanagement = _check_all_intermediate_counters(child)
                if loadmanagement == True:
                    return True
        # Wenn alle durchgegangen wurden und das Lastamangement nicht aktiv geworden ist.
        else:
            return False
    except Exception as e:
        log.exception_logging(e)

def _get_counters_to_check(chargepoint):
    """ ermittelt alle Zähler, die für das Lastmanagement des angegebenen Ladepunkts relevant sind.

    Parameter
    ---------
    chargepoint: class
        Ladepunkt

    Return
    ------
    counters: list
        Liste der gesuchten Zähler
    """
    try:
        counters.clear()
        _look_for_object(data.counter_data["all"].data["get"]["hierarchy"][0], "cp", chargepoint.cp_num)
        return counters
    except Exception as e:
        log.exception_logging(e)

def _look_for_object(child, object, num):
    """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle Zähler in diesem Pfad der Liste anhängt.

    Parameter
    ---------
    child: object
        Zweig, der als nächstes durchsucht werden soll
    object: str "cp"/"counter"
        soll nach einem Ladepunkt oder einem Zähler in der Liste gesucht werden.
    num: int
        Nummer des gesuchten Ladepunkts/Zählers

    Return
    ------
    True/False: Ladepunkt wurde gefunden.
    """
    try:
        parent = child["id"]
        for child in child["children"]:
            if object == "cp":
                if "cp" in child["id"]:
                    if child["id"][2:] == str(num):
                        counters.append(parent)
                        return True
                    else:
                        continue
            elif object == "counter":
                if "counter" in child["id"]:
                    if child["id"][7:] == str(num):
                        return child
            else:
                if len(child["children"]) != 0:
                    found = _look_for_object(child, object, num)
                    if found != False:
                        if object == "cp":
                            counters.append(parent)
                            return True
                    elif object == "counter":
                        return found
        else:
            return False
    except Exception as e:
        log.exception_logging(e)

def _get_all_cp_connected_to_counter(child):
    """ Rekursive Funktion, die alle Ladepunkte ermittelt, die an den angegebenen Zähler angeschlossen sind.

    Parameter
    ---------
    child: object
        Zähler, dessen Ladepunkte ermittelt werden sollen
    """
    # Alle Objekte der Ebene durchgehen
    for child in child["children"]:
        if "cp" in child["id"]:
            chargepoints.append(child["id"])
        # Wenn das Objekt noch Kinder hat, diese ebenfalls untersuchen.
        elif len(child["children"]) != 0:
            _get_all_cp_connected_to_counter(child)

# Überprüfen der Werte

def _loadmanagement_for_evu(current_used, required_power, required_current, phases):
    """ führt die Überprüfung für das Lastmanagement der EVU durch und prüft dabei die maximale Stromstärke, maximalen Bezug und maximale Schieflast, falls aktiv.

    Parameter
    ---------
    current_used: list
        genutzter Strom
    required_power: float
        Leistung, mit der geladen werden soll
    required_current: list
        Stromstärke, mit der geladen werden soll
    phases: int
        Phasen, mit denen geladen werden soll
    Return
    ------
    loadmanagement, consumption_left, current_used: bool, int, list
        Lastmanagement aktiv/inaktiv, verbleibende verfügbare Leistung, genutzter Strom
    """
    global max_current_overshoot
    global max_overshoot_counter
    global max_overshoot_phase
    # Wenn das Lastmanagement einmal aktiv gesetzt wurde, darf es nicht mehr zurück gesetzt werden.
    loadmanagement_all_conditions = False
    loadmanagement, consumption_left = _check_max_power(required_power)
    if loadmanagement == True:
        loadmanagement_all_conditions = True
        overshoot = (consumption_left*-1) /230 / phases
        if max_current_overshoot < overshoot:
            max_current_overshoot = overshoot
            max_overshoot_counter = "counter0"
            max_overshoot_phase = 0
    loadmanagement, current_used_counter, overshoot, phase = _check_max_current("counter0", required_current, phases)
    if loadmanagement == False:
        current_used["counter0"] = current_used_counter
    else:
        loadmanagement_all_conditions = True
        if max_current_overshoot < overshoot:
            max_current_overshoot = overshoot
            max_overshoot_counter = "counter0"
            max_overshoot_phase = phase
    loadmanagement, overshoot, phase = _check_unbalanced_load(current_used_counter)
    if loadmanagement == True:
        loadmanagement_all_conditions = True
        if max_current_overshoot < overshoot:
            max_current_overshoot = overshoot
            max_overshoot_counter = "counter0"
            max_overshoot_phase = phase
    return loadmanagement_all_conditions, consumption_left, current_used

def _check_max_power(required_power):
    """ prüft, dass die maximale Leistung nicht überschritten wird.

    Parameter
    ---------
    required_power: int
        benötigte Leistung
    Return
    ------
    loadmanagement, consumption_left: bool, int
        Lastmanagement aktiv/inaktiv, verbleibende verfügbare Leistung
    """
    try:
        consumption_left = data.counter_data["counter0"].data["set"]["consumption_left"] - required_power
        if consumption_left >= 0:
            return False, consumption_left
        else:
            log.message_debug_log("warning", "Benoetigte Leistung "+str(required_power)+" ueberschreitet den zulaessigen Bezug um "+str((consumption_left*-1))+"W.")
            return True, consumption_left
    except Exception as e:
        log.exception_logging(e)

def _check_max_current(counter, required_current, phases):
    """ prüft, ob die maximale Stromstärke aller Phasen eingehalten wird.

    Parameter
    ---------
    counter: str
        Zähler, der geprüft werden soll
    required_current: list
        Stromstärke, mit der geladen werden soll
    phases: int
        Phasen, mit denen geladen werden soll
    Return
    ------
    loadmanagement: bool
        Lastmanagement aktiv/inaktiv
    current_used: list
        Verwendeter Strom 
    max_current_overshoot: float
        maximale Überschreitung des zulässigen Stroms
    phase: int
        Phase, die den höchsten Strom verbraucht
    """
    current_used = [0, 0, 0]
    required_current_phases = [required_current]*phases + [0]*(3-phases) # erzeugt eine Liste mit der Stromstärke als Wert für die Anzahl der Phasen, der Rest wird mit 0 aufgefüllt
    max_current_overshoot = 0
    try:
        for n in range(phases):
            current_used[n] = data.counter_data[counter].data["set"]["current_used"][n] + required_current_phases[n]
            if current_used[n] < data.counter_data[counter].data["config"]["max_current"][n]:
                loadmanagement = False
            else:
                if (current_used[n]-data.counter_data[counter].data["config"]["max_current"][n]) > max_current_overshoot:
                    max_current_overshoot = current_used[n]-data.counter_data[counter].data["config"]["max_current"][n]
                loadmanagement = True
                log.message_debug_log("warning", "Benoetigte Stromstaerke "+str(required_current[n])+" ueberschreitet die zulaessige Stromstaerke an Phase "+str(n)+ " um "+str((current_used[n]*-1))+"A.")
                break
        return loadmanagement, current_used, max_current_overshoot, current_used.index(max(current_used))
    except Exception as e:
        log.exception_logging(e)

def _check_unbalanced_load(current_used):
    """ prüft, ob die Schieflastbegrenzug aktiv ist und ob diese eingehalten wird.

    Parameter
    ---------
    current_used: list
        Strom, der gebraucht wird
    Return
    ------
    bool: Lastmanagement aktiv/inaktiv
    max_current_overshoot: maximale Überschreitung der Stromstärke
    int: Phase, die den höchsten Strom verbraucht
    """
    max_current_overshoot = 0
    try:
        if data.general_data["general"].data["chargemode_config"]["unbalanced_load"] == True:
            min_current = min(current_used)
            max_current = max(current_used)
            if (max_current - min_current) < data.general_data["general"].data["chargemode_config"]["unbalanced_load_limit"]:
                return False, None, 0
            else:
                max_current_overshoot = (max_current - min_current) - data.general_data["general"].data["chargemode_config"]["unbalanced_load_limit"]
                log.message_debug_log("warning", "Schieflast wurde ueberschritten.")
                return True, max_current_overshoot, current_used.index(max_current)
    except Exception as e:
        log.exception_logging(e)
