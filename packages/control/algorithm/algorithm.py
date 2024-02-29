import logging

from control import counter
from control import data
from control.algorithm import common
from control.algorithm.additional_current import AdditionalCurrent
from control.algorithm.min_current import MinCurrent
from control.algorithm.no_current import NoCurrent
from control.algorithm.surplus_controlled import SurplusControlled

log = logging.getLogger(__name__)


class Algorithm:
    def __init__(self):
        self.additional_current = AdditionalCurrent()
        self.min_current = MinCurrent()
        self.no_current = NoCurrent()
        self.surplus_controlled = SurplusControlled()

    def calc_current(self) -> None:
        """ Einstiegspunkt in den Regel-Algorithmus
        """
        try:
            log.info("# Algorithmus")
            self.evu_counter = data.data.counter_all_data.get_evu_counter()
            self._check_auto_phase_switch_delay()
            self.surplus_controlled.check_submode_pv_charging()
            common.reset_current()
            log.info("**Mindestrom setzen**")
            self.min_current.set_min_current()
            log.info("**Sollstrom setzen**")
            common.reset_current_to_target_current()
            self.additional_current.set_additional_current([0, 8])
            counter.limit_raw_power_left_to_surplus(self.evu_counter.calc_raw_surplus())
            self.surplus_controlled.check_switch_on()
            if self.evu_counter.data.set.surplus_power_left > 0:
                log.info("**PV-geführten Strom setzen**")
                common.reset_current_to_target_current()
                self.surplus_controlled.set_required_current_to_max()
                self.surplus_controlled.set_surplus_current([6, 12])
            else:
                log.info("**Keine Leistung für PV-geführtes Laden übrig.**")
            self.no_current.set_no_current()
            self.no_current.set_none_current()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _check_auto_phase_switch_delay(self) -> None:
        """ geht alle LP durch und prüft, ob eine Ladung aktiv ist, ob automatische Phasenumschaltung
        möglich ist und ob ob ein Timer gestartet oder geChargemode.STOPpt werden muss oder ob
        ein Timer abgelaufen ist.
        """
        for cp in data.data.cp_data.values():
            try:
                if cp.data.set.charging_ev != -1:
                    charging_ev = cp.data.set.charging_ev_data
                    control_parameter = cp.data.control_parameter
                    if cp.cp_ev_chargemode_support_phase_switch():
                        # Gibt die Stromstärke und Phasen zurück, mit denen nach der Umschaltung geladen werden
                        # soll. Falls keine Umschaltung erforderlich ist, werden Strom und Phasen, die übergeben
                        # wurden, wieder zurückgegeben.
                        log.debug(f"Ladepunkt {cp.num}: Prüfen, ob Phasenumschaltung durchgeführt werden soll.")
                        phases, current, message = charging_ev.auto_phase_switch(
                            cp.data.control_parameter,
                            cp.num,
                            cp.data.get.currents,
                            cp.data.get.power,
                            cp.template.data.max_current_single_phase,
                            cp.get_max_phase_hw(),
                            cp.data.control_parameter.limit)
                        if message is not None:
                            cp.data.get.state_str = message
                        # Nachdem im Automatikmodus die Anzahl Phasen bekannt ist, Einhaltung des Maximalstroms
                        # prüfen.
                        required_current = cp.check_min_max_current(current, control_parameter.phases)
                        cp.data.control_parameter.required_current = required_current
                        cp.data.control_parameter.phases = phases
                        cp.set_required_currents(required_current)
            except Exception:
                log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.num}")
