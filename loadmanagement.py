""" Lastmangement
"""

import data
import log


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
    try:
        counters = _get_counters_to_check(chargepoint)
        # Stromstärke merken, wenn das Lastmanagement nicht aktiv wird, wird nach der Prüfung die neue verwendete Stromstärke gesetzt.
        for counter in counters[:-1]:
            loadmanagement, current_used = _check_max_current(counter, required_current, phases)
            if loadmanagement == False:
                current_used[counter] = current_used
            else:
                break
        # Wenn das Lastamanagement bei den Zwischenzählern nicht aktiv wurde, für den EVU-Zähler max. Leistung, max. Stromstärke und Schieflast überprüfen.
        else:
            loadmanagement, consumption_left = _check_max_power(required_power)
            if loadmanagement == False:
                loadmanagement, current_used = _check_max_current("counter0", required_current, phases)
                if loadmanagement == False:
                    current_used["counter0"] = current_used
                    loadmanagement = _check_unbalanced_load(current_used)

        # Werte bei erfolgreichem Lastamanagement schreiben
        if loadmanagement == False:
            data.counter_data["counter0"].data["set"]["consumption_left"] = consumption_left
            log.message_debug_log("debug", str(data.counter_data["counter0"].data["set"]["consumption_left"])+"W EVU-Bezugs-Leistung, die fuer die folgenden Durchlaufe uebrig ist.")
            for counter in current_used:
                data.counter_data[counter].data["set"]["current_used"] = current_used[counter]
        data.counter_data["all"].data["set"]["loadmanagement"] = loadmanagement
        return data.counter_data["all"].data["set"]["loadmanagement"]
    except Exception as e:
        log.exception_logging(e)

def loadmanagement_for_counters():
    """ überprüft bei allen Zählern, ob die Maximal-Werte eingehalten werden.

    Return
    ------
    True/False: Lastmanagement aktiv/inaktiv
    """
    try:
        # Für den EVU-Zähler max. Leistung, max. Stromstärke und Schieflast überprüfen.
        loadmanagement = _check_max_power(0)[0]
        if loadmanagement == False:
            loadmanagement, current_used = _check_max_current("counter0", 0, 0)
            if loadmanagement == False:
                loadmanagement = _check_unbalanced_load(current_used)
                if loadmanagement == False:
                    # Überprüfung der Zwischenzähler
                    loadmanagement = _check_all_intermediate_counters(data.counter_data["all"].data["get"]["hierarchy"][0])
        data.counter_data["all"].data["set"]["loadmanagement"] = loadmanagement
        return loadmanagement
    except Exception as e:
        log.exception_logging(e)

def _check_all_intermediate_counters(child):
    """ Rekursive Funktion, die für alle Zwischenzähler prüft, ob die Maximal-Stromstärke eingehalten wird.

    Parameter
    ---------
    child: Zweig, der als nächstes durchsucht werden soll
    Return
    ------
    True/False: Lastmanagement aktiv/inaktiv
    """
    try:
        # Alle Objekte der Ebene durchgehen
        for child in child["children"]:
            if "counter" in child["id"]:
                # Wenn Objekt ein Zähler ist, Stromstärke prüfen.
                loadmanagement = _check_max_current(child["id"], 0, 0)
                if loadmanagement == True:
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
        if consumption_left > 0:
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
    
    """
    try:
        current_used = [0, 0, 0]
        required_current_phases = [required_current]*phases + [0]*(3-phases) # erzeugt eine Liste mit der Stromstärke als Wert für die Anzahl der Phasen, der Rest wird mit 0 aufgefüllt
        for n in range(phases):
            current_used[n] = data.counter_data[counter].data["set"]["current_used"][n] + required_current_phases[n]
            if current_used[n] < data.counter_data[counter].data["config"]["max_current"][n]:
                loadmanagement = False
            else:
                loadmanagement = True
                log.message_debug_log("warning", "Benoetigte Stromstaerke "+str(required_current[n])+" ueberschreitet die zulaessige Stromstaerke an Phase "+str(n)+ " um "+str((current_used[n]*-1))+"A.")
                break
        return loadmanagement, current_used
    except Exception as e:
        log.exception_logging(e)

def _check_unbalanced_load(current_used):
    """
    """
    try:
        if data.general_data["general"].data["chargemode_config"]["unbalanced_load"] == True:
            min_current = min(current_used)
            max_current = max(current_used)
            if (max_current - min_current) < data.general_data["general"].data["chargemode_config"]["unbalanced_load_limit"]:
                return False
            else:
                log.message_debug_log("warning", "Schieflast wurde ueberschritten.")
                return True
    except Exception as e:
        log.exception_logging(e)

counters = []

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
        _look_for_cp(data.counter_data["all"].data["get"]["hierarchy"][0], str(chargepoint.cp_num))
        return counters
    except Exception as e:
        log.exception_logging(e)

def _look_for_cp(child, cp_num):
    """ Rekursive Funktion, die alle Zweige durchgeht, bis der entsprechende Ladepunkt gefunden wird und dann alle Zähler in diesem Pfad als Liste zurückgibt.

    Parameter
    ---------
    child: Zweig, der als nächstes durchsucht werden soll
    cp_num: str
        Nummer des gesuchten Ladepunkts

    Return
    ------
    True/False: Ladepunkt wurde gefunden.
    """
    try:
        parent = child["id"]
        for child in child["children"]:
            if "cp" in child["id"]:
                if child["id"][2:] == cp_num:
                    counters.append(parent)
                    return True
                else:
                    continue
            else:
                if len(child["children"]) != 0:
                    found = _look_for_cp(child, cp_num)
                    if found == True:
                        counters.append(parent)
                        return True
        else:
            return False
    except Exception as e:
        log.exception_logging(e)