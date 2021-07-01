"""Allgemeine Einstellungen
"""

import data
import log
import pub


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

    def grid_protection(self):
        """ Wenn der Netschutz konfiguriert ist, wird geprüft, ob die Frequenz außerhalb des Normalbereichs liegt 
        und dann der Netzschutz aktiviert. Bei der Ermittlung des benötigten Stroms im EV-Modul wird geprüft, ob 
        der Netzschutz aktiv ist und dann die Ladung gestoppt.
        """
        try:
            if self.data["grid_protection_configured"] == True:
                frequency = data.data.counter_data["counter0"].data["get"]["frequency"] * 100
                grid_protection_active = self.data["grid_protection_active"]
                if grid_protection_active == False:
                    if 4500 < frequency < 4920 or 5180 < frequency < 5300:
                        self.data["grid_protection_active"] = True
                        pub.pub("openWB/set/general/grid_protection_active", self.data["grid_protection_active"])
                        log.message_debug_log("info", "Netzschutz aktiv! Frequenz: "+str(data.data.counter_data["counter0"].data["get"]["frequency"])+"Hz")
                else:
                    if 4962 < frequency < 5100:
                        self.data["grid_protection_active"] = False
                        pub.pub("openWB/set/general/grid_protection_active", self.data["grid_protection_active"])
                        log.message_debug_log("info", "Netzfrequenz wieder im normalen Bereich. Frequenz: "+str(data.data.counter_data["counter0"].data["get"]["frequency"])+"Hz")
        except Exception as e:
            log.exception_logging(e)