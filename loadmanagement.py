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
    state: bool
    """
    try:
        # Maximale Leistung
        state = False
        consumption_left = data.counter_data["evu"].data["set"]["consumption_left"] - required_power
        if consumption_left > 0:
            state = True
        else:
            # runterregeln
            state = False
            log.message_debug_log("warning", "Benötigte Leistung "+str(required_power)+" überschreitet den zulässigen Bezug um "+str((consumption_left*-1))+"W.")
            return

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
        if state == True:
            data.counter_data["evu"].data["set"]["consumption_left"] = consumption_left
        #data.counter_data["evu"].data["set"]["current_left"] = current_left
        return state
    except Exception as e:
        log.exception_logging(e)
