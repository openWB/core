"""Allgemeine Einstellungen
"""

import log


class general():
    """
    """

    def __init__(self):
        self.data={}


    def get_phases_chargemode(self, chargemode):
        """ gibt die Anazhl Phasen zurück, mit denen im jeweiligen Lademodus geladen wird. 
        Wenn der Lademodus Stop oder Standby ist, wird 0 zurückgegeben, da in diesem Fall 
        die bisher genutzte Phasenzahl weiter genutzt wird, bis der Algorithmus eine Umschaltung vorgibt.

        Parameter
        ---------
        chargemode: str
            Lademodus
        
        Return
        ------
        int: Anzahl Phasen
        """
        try:
            if chargemode == "stop" or chargemode == "standby":
                return 0
            else:
                return self.data["chargemode_config"][chargemode]["phases_to_use"]
        except Exception as e:
            log.exception_logging(e)
            return 1