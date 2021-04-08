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
            data.counter_data["all"].put_stats()
            data.counter_data["counter0"].put_stats()
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    if chargepoint.data["set"]["charging_ev"] != -1:
                            chargepoint.initiate_control_pilot_interruption()
                            chargepoint.initiate_phase_switch(chargepoint)
                            self._update_state(chargepoint)
        except Exception as e:
            log.exception_logging(e)

    def _update_state(self, chargepoint):
        """aktualisiert den Zustand des Ladepunkts.
        """
        try:
            if chargepoint.data["set"]["current"] != 0:
                chargepoint.data["get"]["charge_state"] = True
            else:
                chargepoint.data["get"]["charge_state"] = False
            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/charge_state", chargepoint.data["get"]["charge_state"])
            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/phases_to_use", chargepoint.data["set"]["phases_to_use"])
            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", round(chargepoint.data["set"]["current"], 2))
        except Exception as e:
            log.exception_logging(e)