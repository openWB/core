""" Starten des Lade-Vorgangs
"""

from . import chargelog
from . import data
from ..helpermodules import log
from ..helpermodules import pub
from ..modules.cp import external_openwb
from ..modules.cp import ip_evse
from ..modules.cp import master_eth_framer
from ..modules.cp import modbus_evse
from ..modules.cp import modbus_slave


class process():
    def __init__(self):
        pass

    def process_algorithm_results(self):
        try:
            log.message_debug_log("debug", "# Ladung starten.")
            for cp in data.data.cp_data:
                try:
                    if "cp" in cp:
                        chargepoint = data.data.cp_data[cp]
                        if chargepoint.data["set"]["charging_ev"] != -1:
                            # Ladelog-Daten müssen vor dem Setzen des Stroms gesammelt werden, 
                            # damit bei Phasenumschaltungs-empfindlichen EV sicher noch nicht geladen wurde.
                            chargelog.collect_data(chargepoint)
                            chargepoint.initiate_control_pilot_interruption()
                            chargepoint.initiate_phase_switch()
                            self._update_state(chargepoint)
                        else:
                            # LP, an denen nicht geladen werden darf
                            if chargepoint.data["set"]["charging_ev_prev"] != -1:
                                chargelog.save_data(chargepoint, data.data.ev_data["ev"+str(chargepoint.data["set"]["charging_ev_prev"])], immediately = False)
                            chargepoint.data["set"]["current"] = 0
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", 0)
                        if chargepoint.data["get"]["state_str"] != None:
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/state_str", chargepoint.data["get"]["state_str"])
                        else:
                            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/state_str", "Ladevorgang läuft...")
                        self._start_charging(chargepoint)
                except Exception as e:
                    log.exception_logging(e)
            data.data.pv_data["all"].put_stats()
            data.data.pv_data["all"].print_stats()
            data.data.counter_data["counter0"].put_stats()
        except Exception as e:
            log.exception_logging(e)

    def _update_state(self, chargepoint):
        """aktualisiert den Zustand des Ladepunkts.
        """
        try:
            charging_ev = chargepoint.data["set"]["charging_ev_data"]
            
            current = round(chargepoint.data["set"]["current"], 2)
            # Zur Sicherheit - nach dem der Algorithmus abgeschlossen ist - nochmal die Einhaltung der Stromstärken prüfen.
            current = charging_ev.check_min_max_current(current, charging_ev.data["control_parameter"]["phases"])

            # Wenn bei einem EV, das keine Umschaltung verträgt, vor dem ersten Laden noch umgeschaltet wird, darf kein Strom gesetzt werden.
            if (charging_ev.ev_template.data["prevent_switch_stop"] == True and 
                    charging_ev.data["get"]["charged_since_plugged_counter"] == 0 and 
                    charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] != "0"):
                current = 0

            # Unstimmige Werte loggen
            if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] != "0" and
                    chargepoint.data["get"]["charge_state"] == False and 
                    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] == 0):
                log.message_debug_log("error", "Reservierte Leistung kann am Algorithmus-Ende nicht 0 sein.")
            if (chargepoint.data["set"]["charging_ev_data"].ev_template.data["prevent_switch_stop"] == True and
                    chargepoint.data["get"]["charge_state"] == True and
                    chargepoint.data["set"]["current"] == 0):
                log.message_debug_log("error", "LP"+str(chargepoint.cp_num)+": Ladung wurde trotz verhinderter Unterbrechung gestoppt.")
            
            chargepoint.data["set"]["current"] = current
            pub.pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", current)
            log.message_debug_log("debug", "LP"+str(chargepoint.cp_num)+": set current "+str(current)+" A")
        except Exception as e:
            log.exception_logging(e)

    def _start_charging(self, chargepoint):
        """ setzt den Ladestrom im Ladeleistungs-Modul.

        Parameter
        ---------
        chargepoint: dict
            Ladepunkt, dessen Strom gesetzt werden soll.
        """
        try:
            if "charging_ev_data" in chargepoint.data["set"]:
                charging_ev = chargepoint.data["set"]["charging_ev_data"]
                # Wenn ein EV zugeordnet ist und die Phasenumschaltung aktiv ist, darf kein Strom gesetzt werden.
                if charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] != "0":
                    current = 0
                else:
                    current = chargepoint.data["set"]["current"]
            else:
                current = chargepoint.data["set"]["current"]
            if chargepoint.data["config"]["connection_module"]["selected"] == "external_openwb":
                num = chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["chargepoint"]
                ip_address = chargepoint.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"]
                external_openwb.write_external_openwb(ip_address, num, current)
            elif chargepoint.data["config"]["connection_module"]["selected"] == "daemon":
                # Is handled in lldaemon.py
                pass
            elif chargepoint.data["config"]["connection_module"]["selected"] == "buchse":
                # Is handled in buchse.py
                pass
            elif chargepoint.data["config"]["connection_module"]["selected"] == "masterethframer":
                master_eth_framer.write_master_eth_framer(current)
            elif chargepoint.data["config"]["connection_module"]["selected"] == "ip_evse":
                ip_address = chargepoint.data["config"]["connection_module"]["config"]["ip_evse"]["ip_address"]
                id = chargepoint.data["config"]["connection_module"]["config"]["ip_evse"]["id"]
                ip_evse.write_ip_evse(ip_address, id, current)
            elif chargepoint.data["config"]["connection_module"]["selected"] == "http":
                pass
            elif chargepoint.data["config"]["connection_module"]["selected"] == "modbus_evse":
                modbus_evse.write_modbus_evse(chargepoint)
            elif chargepoint.data["config"]["connection_module"]["selected"] == "modbus_slave":
                modbus_slave.write_modbus_slave(current)
        except Exception as e:
            log.exception_logging(e)

