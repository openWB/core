""" Lastmangement
"""

import data
import log


def loadmanagement(required_power, required_current, phases):
    """ prüft, ob maximale Stromstärke oder Bezug überschritten wurden.

    Parameter
    ---------
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
    try:
        # Maximale Leistung
        consumption_left = data.counter_data["counter0"].data["set"]["consumption_left"] - required_power
        if consumption_left > 0:
            data.counter_data["all"].data["set"]["loadmanagement"] = False
        else:
            data.counter_data["all"].data["set"]["loadmanagement"] = True
            log.message_debug_log("warning", "Benoetigte Leistung "+str(required_power)+" ueberschreitet den zulaessigen Bezug um "+str((consumption_left*-1))+"W.")

        # Maximaler Strom
        current_used = [0, 0, 0]
        required_current_phases = [required_current]*phases + [0]*(3-phases) # erzeugt eine Liste mit der Stromstärke als Wert für die Anzahl der Phasen, der Rest wird mit 0 aufgefüllt
        for n in range(phases):
            current_used[n] = data.counter_data["counter0"].data["set"]["current_used"][n] + required_current_phases[n]
            if current_used[n] < data.counter_data["counter0"].data["config"]["max_current"][n]:
                data.counter_data["all"].data["set"]["loadmanagement"] = False
            else:
                data.counter_data["all"].data["set"]["loadmanagement"] = True
                log.message_debug_log("warning", "Benoetigte Stromstaerke "+str(required_current[n])+" ueberschreitet die zulaessige Stromstaerke an Phase "+str(n)+ " um "+str((current_used[n]*-1))+"A.")
                break

        # Schieflast
        if data.general_data["general"].data["chargemode_config"]["unbalanced_load"] == True:
            min_current = min(current_used)
            max_current = max(current_used)
            if (max_current - min_current) < data.general_data["general"].data["chargemode_config"]["unbalanced_load_limit"]:
                data.counter_data["all"].data["set"]["loadmanagement"] = False
            else:
                data.counter_data["all"].data["set"]["loadmanagement"] = True
                log.message_debug_log("warning", "Schieflast wurde ueberschritten.")


        # Werte bei erfolgreichem Lastamanagement schreiben
        if data.counter_data["all"].data["set"]["loadmanagement"] == False:
            data.counter_data["counter0"].data["set"]["consumption_left"] = consumption_left
            log.message_debug_log("debug", str(data.counter_data["counter0"].data["set"]["consumption_left"])+"W EVU-Bezugs-Leistung, die fuer die folgenden Durchlaufe uebrig ist.")
            data.counter_data["counter0"].data["set"]["current_used"] = current_used
        return data.counter_data["all"].data["set"]["loadmanagement"]
    except Exception as e:
        log.exception_logging(e)