"""Allgemeine Einstellungen
"""
import logging
import random

from control import data
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


class General:
    """
    """

    def __init__(self):
        self.data = {"grid_protection_active": False}

    def get_phases_chargemode(self, chargemode: str) -> int:
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
        except Exception:
            log.exception("Fehler im General-Modul")
            return 1

    def grid_protection(self):
        """ Wenn der Netschutz konfiguriert ist, wird geprüft, ob die Frequenz außerhalb des Normalbereichs liegt
        und dann der Netzschutz aktiviert. Bei der Ermittlung des benötigten Stroms im EV-Modul wird geprüft, ob
        der Netzschutz aktiv ist und dann die Ladung gestoppt.
        """
        try:
            evu_counter = data.data.counter_data["all"].get_evu_counter()
            if self.data["grid_protection_configured"]:
                frequency = data.data.counter_data[evu_counter].data["get"]["frequency"] * 100
                grid_protection_active = self.data["grid_protection_active"]
                if not grid_protection_active:
                    if 4500 < frequency < 4920:
                        self.data["grid_protection_random_stop"] = random.randint(
                            1, 90)
                        self.data["grid_protection_timestamp"] = timecheck.create_timestamp(
                        )
                        self.data["grid_protection_active"] = True
                        Pub().pub("openWB/set/general/grid_protection_timestamp",
                                  self.data["grid_protection_timestamp"])
                        Pub().pub("openWB/set/general/grid_protection_random_stop",
                                  self.data["grid_protection_random_stop"])
                        Pub().pub("openWB/set/general/grid_protection_active",
                                  self.data["grid_protection_active"])
                        log.info("Netzschutz aktiv! Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data["get"]["frequency"])+"Hz")
                    if 5180 < frequency < 5300:
                        self.data["grid_protection_random_stop"] = 0
                        self.data["grid_protection_timestamp"] = "0"
                        self.data["grid_protection_active"] = True
                        Pub().pub("openWB/set/general/grid_protection_timestamp",
                                  self.data["grid_protection_timestamp"])
                        Pub().pub("openWB/set/general/grid_protection_random_stop",
                                  self.data["grid_protection_random_stop"])
                        Pub().pub("openWB/set/general/grid_protection_active",
                                  self.data["grid_protection_active"])
                        log.info("Netzschutz aktiv! Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data["get"]["frequency"])+"Hz")
                else:
                    if 4962 < frequency < 5100:
                        self.data["grid_protection_active"] = False
                        Pub().pub("openWB/set/general/grid_protection_active",
                                  self.data["grid_protection_active"])
                        log.info("Netzfrequenz wieder im normalen Bereich. Frequenz: " +
                                 str(data.data.counter_data[evu_counter].data["get"]["frequency"])+"Hz")
                        Pub().pub(
                            "openWB/set/general/grid_protection_timestamp", "0")
                        Pub().pub(
                            "openWB/set/general/grid_protection_random_stop", 0)
        except Exception:
            log.exception("Fehler im General-Modul")
