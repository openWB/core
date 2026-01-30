import logging
from typing import List

from control import data
from control.algorithm import common
from control.algorithm.additional_current import AdditionalCurrent
from control.algorithm.bidi_charging import Bidi
from control.algorithm.min_current import MinCurrent
from control.algorithm.no_current import NoCurrent
from control.algorithm.surplus_controlled import SurplusControlled
from control.chargepoint.chargepoint import Chargepoint

log = logging.getLogger(__name__)


class Algorithm:
    def __init__(self):
        self.additional_current = AdditionalCurrent()
        self.bidi = Bidi()
        self.min_current = MinCurrent()
        self.no_current = NoCurrent()
        self.surplus_controlled = SurplusControlled()

    def calc_current(self) -> None:
        """ Einstiegspunkt in den Regel-Algorithmus
        """
        log.info("# Algorithmus")
        common.reset_current()
        for next_low_power_group, next_full_power_group in data.data.counter_all_data.prio_groups_generator():
            try:
                if next_low_power_group is not None:
                    self._check_auto_phase_switch_delay(next_low_power_group)
                    self.surplus_controlled.check_submode_pv_charging(next_low_power_group)
                    self.min_current.set_min_current(next_low_power_group)
                if next_full_power_group is not None:
                    self._check_auto_phase_switch_delay(next_full_power_group)
                    self.surplus_controlled.check_submode_pv_charging(next_full_power_group)
                    self.min_current.set_min_current(next_full_power_group)
                    self.additional_current.set_additional_current(next_full_power_group)
                    self.surplus_controlled.set_surplus_current(next_full_power_group)
                if next_low_power_group is not None:
                    self.additional_current.set_additional_current(next_low_power_group)
                    self.surplus_controlled.set_surplus_current(next_low_power_group)
            except Exception:
                log.exception("Fehler im Algorithmus-Modul")
        self.bidi.set_bidi()
        self.no_current.set_no_current()
        self.no_current.set_none_current()

    def _check_auto_phase_switch_delay(self, cps: List[Chargepoint]) -> None:
        """ geht alle LP durch und prüft, ob eine Ladung aktiv ist, ob automatische Phasenumschaltung
        möglich ist und ob ob ein Timer gestartet oder gestoppt werden muss oder ob
        ein Timer abgelaufen ist.
        """
        for cp in cps:
            try:
                if cp.data.control_parameter.required_current != 0:
                    charging_ev = cp.data.set.charging_ev_data
                    control_parameter = cp.data.control_parameter
                    if control_parameter.template_phases == 0 and cp.cp_state_hw_support_phase_switch():
                        # Gibt die Stromstärke und Phasen zurück, mit denen nach der Umschaltung geladen werden
                        # soll. Falls keine Umschaltung erforderlich ist, werden Strom und Phasen, die übergeben
                        # wurden, wieder zurückgegeben.
                        log.debug(f"Ladepunkt {cp.num}: Prüfen, ob Phasenumschaltung durchgeführt werden soll.")
                        phases, current, message = charging_ev.auto_phase_switch(
                            cp.data.set.charge_template,
                            cp.data.control_parameter,
                            cp.num,
                            cp.data.get.evse_current,
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
