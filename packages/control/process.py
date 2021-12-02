""" Starten des Lade-Vorgangs
"""
import threading
from typing import List

from control import chargelog
from control import data
from helpermodules import log
from helpermodules.pub import Pub


class process:
    def __init__(self):
        pass

    def process_algorithm_results(self):
        try:
            log.MainLogger().debug("# Ladung starten.")
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
                                chargelog.save_data(
                                    chargepoint, data.data.ev_data
                                    ["ev" + str(chargepoint.data["set"]["charging_ev_prev"])],
                                    immediately=False)
                            chargepoint.data["set"]["current"] = 0
                            Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", 0)
                        if chargepoint.data["get"]["state_str"] is not None:
                            Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/get/state_str",
                                      chargepoint.data["get"]["state_str"])
                        else:
                            Pub().pub(
                                "openWB/set/chargepoint/" + str(chargepoint.cp_num) + "/get/state_str",
                                "Ladevorgang läuft...")
                        self._start_charging(chargepoint)
                except Exception:
                    log.MainLogger().exception("Fehler im Process-Modul fuer Ladepunkt "+str(cp))
            data.data.pv_data["all"].put_stats()
            data.data.pv_data["all"].print_stats()
            data.data.counter_data[data.data.counter_data["all"].get_evu_counter()].put_stats()
        except Exception:
            log.MainLogger().exception("Fehler im Process-Modul")

    def _update_state(self, chargepoint):
        """aktualisiert den Zustand des Ladepunkts.
        """
        try:
            charging_ev = chargepoint.data["set"]["charging_ev_data"]

            current = round(chargepoint.data["set"]["current"], 2)
            # Zur Sicherheit - nach dem der Algorithmus abgeschlossen ist - nochmal die Einhaltung der Stromstärken
            # prüfen.
            current = charging_ev.check_min_max_current(current, charging_ev.data["control_parameter"]["phases"])

            # Wenn bei einem EV, das keine Umschaltung verträgt, vor dem ersten Laden noch umgeschaltet wird, darf kein
            # Strom gesetzt werden.
            if (charging_ev.ev_template.data["prevent_switch_stop"] and
                    chargepoint.data["set"]["log"]["charged_since_plugged_counter"] == 0 and
                    charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] != "0"):
                current = 0

            # Unstimmige Werte loggen
            if (charging_ev.data["control_parameter"]["timestamp_switch_on_off"] != "0" and
                    not chargepoint.data["get"]["charge_state"] and
                    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] == 0):
                log.MainLogger().error("Reservierte Leistung kann am Algorithmus-Ende nicht 0 sein.")
            if (chargepoint.data["set"]["charging_ev_data"].ev_template.data["prevent_switch_stop"] and
                    chargepoint.data["get"]["charge_state"] and
                    chargepoint.data["set"]["current"] == 0):
                log.MainLogger().error(
                    "LP"+str(chargepoint.cp_num)+": Ladung wurde trotz verhinderter Unterbrechung gestoppt.")

            chargepoint.data["set"]["current"] = current
            Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num)+"/set/current", current)
            log.MainLogger().debug("LP"+str(chargepoint.cp_num)+": set current "+str(current)+" A")
        except Exception:
            log.MainLogger().exception("Fehler im Process-Modul")

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

            modules_threads = []  # type: List[threading.Thread]
            for item in data.data.cp_data:
                try:
                    if "cp" in item:
                        thread = None
                        chargepoint_module = data.data.cp_data[item].chargepoint_module
                        thread = threading.Thread(target=chargepoint_module.set_current, args=(current,))
                        if thread is not None:
                            modules_threads.append(thread)
                except Exception:
                    log.MainLogger().exception("Fehler im loadvars-Modul")
            if modules_threads:
                for thread in modules_threads:
                    thread.start()

                # Wait for all to complete
                for thread in modules_threads:
                    thread.join(timeout=3)

                for thread in modules_threads:
                    if thread.is_alive():
                        log.MainLogger().error(
                            thread.name +
                            " konnte nicht innerhalb des Timeouts die Werte senden.")
        except Exception:
            log.MainLogger().exception("Fehler im Process-Modul")
