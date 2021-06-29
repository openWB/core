""" Starten des Lade-Vorgangs
"""

import chargelog
import data
import log
import pub

class charge():
    def __init__(self):
        pass

    def start_charging(self):
        try:
            log.message_debug_log("debug", "# Ladung starten.")
            for cp in data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.cp_data[cp]
                        if chargepoint.data["set"]["charging_ev"] != -1:
                            chargelog.collect_data(chargepoint)
                            chargepoint.initiate_control_pilot_interruption()
                            chargepoint.initiate_phase_switch()
                            self._update_state(chargepoint)
                        else:
                            # LP, an denen nicht geladen werden darf
                            if chargepoint.data["set"]["charging_ev_prev"] != -1:
                                chargelog.save_data(chargepoint, data.ev_data["ev"+str(chargepoint.data["set"]["charging_ev_prev"])], immediately = False)
                            chargepoint.data["set"]["current"] = 0
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", 0)
                        if chargepoint.data["get"]["state_str"] != None:
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/state_str", chargepoint.data["get"]["state_str"])
                        else:
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/state_str", "Ladevorgang läuft...")
                except Exception as e:
                    log.exception_logging(e)
            data.pv_data["all"].put_stats()
            data.pv_data["all"].print_stats()
            data.counter_data["counter0"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _update_state(self, chargepoint):
        """aktualisiert den Zustand des Ladepunkts.
        """
        try:
            charging_ev = chargepoint.data["set"]["charging_ev_data"]
            # Keine Umschaltung im Gange
            if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] == "0":
                current = round(chargepoint.data["set"]["current"], 2)
                # Zur Sicherheit - nach dem der Algorithmus abgeschlossen ist - nochmal die Einhaltung der Stromstärken prüfen.
                current = charging_ev.check_min_max_current(current, charging_ev.data["control_parameter"]["phases"])

                # Unstimmige Werte loggen
                if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] != "0" and
                        chargepoint.data["get"]["charge_state"] == False and 
                        data.pv_data["all"].data["set"]["reserved_evu_overhang"] == 0):
                    log.message_debug_log("error", "Reservierte Leistung kann am Algorithmus-Ende nicht 0 sein.")
                if (chargepoint.data["set"]["charging_ev_data"].ev_template.data["prevent_switch_stop"] == True and
                        chargepoint.data["get"]["charge_state"] == True and
                        chargepoint.data["set"]["current"] == 0):
                    log.message_debug_log("error", "LP"+str(chargepoint.cp_num)+": Ladung wurde trotz verhinderter Unterbrechung gestoppt.")
                
                pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", current)
                log.message_debug_log("debug", "LP"+str(chargepoint.cp_num)+": set current "+str(current)+" A")
        except Exception as e:
            log.exception_logging(e)