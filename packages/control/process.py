""" Starten des Lade-Vorgangs
"""
import logging
import threading
from typing import List

from control.chargelog import chargelog
from control.chargepoint import chargepoint
from control import data
from control.chargepoint.chargepoint_state import ChargepointState
from helpermodules.pub import Pub
from helpermodules.utils._thread_handler import joined_thread_handler

log = logging.getLogger(__name__)


class Process:
    def __init__(self) -> None:
        pass

    def process_algorithm_results(self) -> None:
        try:
            modules_threads: List[threading.Thread] = []
            log.info("# Ladung starten.")
            for cp in data.data.cp_data.values():
                try:
                    control_parameter = cp.data.control_parameter
                    cp.remember_previous_values()
                    if cp.data.set.charging_ev != -1:
                        # Ladelog-Daten müssen vor dem Setzen des Stroms gesammelt werden,
                        # damit bei Phasenumschaltungs-empfindlichen EV sicher noch nicht geladen wurde.
                        chargelog.collect_data(cp)
                        cp.initiate_control_pilot_interruption()
                        cp.initiate_phase_switch()
                        if control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED and cp.data.set.current != 0:
                            control_parameter.state = ChargepointState.CHARGING_ALLOWED
                        self._update_state(cp)
                    else:
                        # LP, an denen nicht geladen werden darf
                        if cp.data.set.charging_ev_prev != -1:
                            chargelog.save_interim_data(
                                cp, data.data.ev_data
                                ["ev" + str(cp.data.set.charging_ev_prev)],
                                immediately=False)
                        cp.data.set.current = 0
                        Pub().pub("openWB/set/chargepoint/"+str(cp.num)+"/set/current", 0)
                        control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
                    if cp.data.get.state_str is not None:
                        Pub().pub("openWB/set/chargepoint/"+str(cp.num)+"/get/state_str",
                                  cp.data.get.state_str)
                    else:
                        Pub().pub(
                            f"openWB/set/chargepoint/{cp.num}/get/state_str",
                            "Ladevorgang wurde gestartet... (bei Problemen: Prüfe bitte zuerst in den Einstellungen"
                            " 'Ladeeinstellungen' und 'Konfiguration'.)")
                    modules_threads.append(self._start_charging(cp))
                except Exception:
                    log.exception("Fehler im Process-Modul für Ladepunkt "+str(cp))

            if modules_threads:
                joined_thread_handler(modules_threads, 3)
        except Exception:
            log.exception("Fehler im Process-Modul")

    def _update_state(self, chargepoint: chargepoint.Chargepoint) -> None:
        """aktualisiert den Zustand des Ladepunkts.
        """
        charging_ev = chargepoint.data.set.charging_ev_data

        current = round(chargepoint.data.set.current, 2)
        # Zur Sicherheit - nach dem der Algorithmus abgeschlossen ist - nochmal die Einhaltung der Stromstärken
        # prüfen.
        current = chargepoint.check_min_max_current(current, chargepoint.data.control_parameter.phases)

        # Wenn bei einem EV, das keine Umschaltung verträgt, vor dem ersten Laden noch umgeschaltet wird, darf kein
        # Strom gesetzt werden.
        if (charging_ev.ev_template.data.prevent_phase_switch and
                chargepoint.data.set.log.imported_since_plugged == 0 and
                chargepoint.data.control_parameter.state == ChargepointState.PERFORMING_PHASE_SWITCH):
            current = 0

        # Unstimmige Werte loggen
        if (chargepoint.data.control_parameter.state == ChargepointState.SWITCH_ON_DELAY and
                data.data.counter_all_data.get_evu_counter().data.set.reserved_surplus == 0):
            log.error("Reservierte Leistung kann am Algorithmus-Ende nicht 0 sein.")
        if (chargepoint.data.set.charging_ev_data.ev_template.data.prevent_phase_switch and
                chargepoint.data.get.charge_state and
                chargepoint.data.set.current == 0):
            log.error(
                "LP"+str(chargepoint.num)+": Ladung wurde trotz verhinderter Unterbrechung gestoppt.")

        # Wenn ein EV zugeordnet ist und die Phasenumschaltung aktiv ist, darf kein Strom gesetzt werden.
        if (chargepoint.data.control_parameter.timestamp_perform_phase_switch is not None or
                chargepoint.data.control_parameter.state == ChargepointState.PERFORMING_PHASE_SWITCH):
            current = 0

        chargepoint.data.set.current = current
        Pub().pub("openWB/set/chargepoint/"+str(chargepoint.num)+"/set/current", current)
        log.info(f"LP{chargepoint.num}: set current {current} A, "
                 f"state {ChargepointState(chargepoint.data.control_parameter.state).name}")

    def _start_charging(self, chargepoint: chargepoint.Chargepoint) -> threading.Thread:
        return threading.Thread(target=chargepoint.chargepoint_module.set_current,
                                args=(chargepoint.data.set.current,),
                                name=f"set current cp{chargepoint.chargepoint_module.config.id}")
