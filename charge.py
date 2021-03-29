""" Starten des Lade-Vorgangs
"""

import data
import log
import pub

class charge():
    def __init__(self):
        pass

    def start_charging(self):
        try:
            log.message_debug_log("debug", "# Ladung starten.")
            data.pv_data["pv"].put_stats()
            data.counter_data["evu"].put_stats()
            for cp in data.cp_data:
                chargepoint = data.cp_data[cp]
                if "set" in chargepoint.data:
                    if "charging_ev" in chargepoint.data["set"]:
                        # CP-Unterbrechung durchführen?
                        # Phasenumschaltung erforderlich?
                        if chargepoint.data["get"]["phases_in_use"] != chargepoint.data["set"]["phases_to_use"]:
                            #perform phase switch
                            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/phases_to_use", chargepoint.data["set"]["phases_to_use"])
                            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", chargepoint.data["set"]["charging_ev"].data["control_parameter"]["required_current"])
                        if chargepoint.data["set"]["current"]  != 0:
                            chargepoint.data["get"]["charge_state"] == True
                        else:
                            chargepoint.data["get"]["charge_state"] == False
                        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/get/charge_state", chargepoint.data["get"]["charge_state"])
                        pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/get/power_all", (chargepoint.data["set"]["phases_to_use"]*chargepoint.data["set"]["current"]*230))
        except Exception as e:
            log.exception_logging(e)