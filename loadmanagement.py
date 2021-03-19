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
        consumption_left = data.counter_data["evu"].data["set"]["consumption_left"] - required_power
        if consumption_left > 0:
            data.counter_data["evu"].data["set"]["loadmanagement"] = False
        else:
            data.counter_data["evu"].data["set"]["loadmanagement"] = True
            log.message_debug_log("warning", "Benötigte Leistung "+str(required_power)+" überschreitet den zulässigen Bezug um "+str((consumption_left*-1))+"W.")
            

        # Maximaler Strom
        # current_left = [0, 0, 0]
        # required_current_phases = [required_current]*phases + [0]*(3-phases)
        # for n in range(phases):
        #     current_left[n] = data.counter_data["evu"].data["set"]["current_left"][n] - required_current_phases[n]
        #     if current_left[n] > 0:
        #         state = True
        #     else:
        #         # runterregeln
        #         state = False
        #         #log.message_debug_log("warning", "LP "+str(chargepoint.cp_num)+": Benötigte Stromstärke "+str(required_current[n])+" überschreitet die zulässige Stromstärke der EVU an Phase "+str(n)+ "um "+str((current_left[n]*-1))+"A.")
        #         return

        # Werte bei erfolgreichem Lastamanagement schreiben
        if data.counter_data["evu"].data["set"]["loadmanagement"] == False:
            data.counter_data["evu"].data["set"]["consumption_left"] = consumption_left
            log.message_debug_log("debug", str(data.counter_data["evu"].data["set"]["consumption_left"])+"W EVU-Bezugs-Leistung, die fuer die folgenden Durchlaufe uebrig ist.")
        #data.counter_data["evu"].data["set"]["current_left"] = current_left
        return data.counter_data["evu"].data["set"]["loadmanagement"]
    except Exception as e:
        log.exception_logging(e)