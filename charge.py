""" Starten des Lade-Vorgangs
"""

import requests
import time
from pymodbus.client.sync import ModbusTcpClient

import data
import log
import pub

class charge():
    def __init__(self):
        pass

    def start_charging(self):
        try:
            log.message_debug_log("debug", "# Ladung starten.")
            data.pv_data["all"].put_stats()
            data.pv_data["all"].print_stats()
            data.counter_data["counter0"].put_stats()
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    if chargepoint.data["set"]["charging_ev"] != -1:
                        chargepoint.initiate_control_pilot_interruption()
                        chargepoint.initiate_phase_switch()
                        self._update_state(chargepoint)
                    else:
                        # LP, an denen nicht geladen werden darf
                        if chargepoint.data["set"]["current"] != 0:
                            chargepoint.data["set"]["current"] = 0
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", 0)
        except Exception as e:
            log.exception_logging(e)

    def _update_state(self, chargepoint):
        """aktualisiert den Zustand des Ladepunkts.
        """
        try:
            current = round(chargepoint.data["set"]["current"], 2)
            # Zur Sicherheit - nach dem der Algorithmus abgeschlossen ist - nochmal die Einhaltung der Stromstärken prüfen.
            current = chargepoint.data["set"]["charging_ev"].check_min_max_current(current, chargepoint.data["set"]["charging_ev"].data["control_parameter"]["phases"])
            if (chargepoint.data["set"]["charging_ev"].data["control_parameter"]["timestamp_switch_on_off"] != "0" and
                    chargepoint.data["get"]["charge_state"] == False and 
                    data.pv_data["all"].data["set"]["overhang_power_left"] == 0):
                log.message_debug_log("error", "Reservierte Leistung kann am Algorithmus-Ende nicht 0 sein.")
            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", current)
        except Exception as e:
            log.exception_logging(e)