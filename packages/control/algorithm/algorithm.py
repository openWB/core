import logging

from control import counter
from control import data
from control.algorithm import common
from control.algorithm.additional_current import AdditionalCurrent
from control.algorithm.min_current import MinCurrent
from control.algorithm.no_current import NoCurrent
from control.algorithm.surplus_controlled import SurplusControlled
from control.chargemode import Chargemode
from helpermodules.pub import Pub
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
            log.debug("# Algorithmus")
            self.evu_counter = data.data.counter_all_data.get_evu_counter()
            self._check_auto_phase_switch_delay()
            self.surplus_controlled.check_submode_pv_charging()
            common.reset_current()
            common.reset_current_to_target_current()
            log.debug("**Mindestrom setzen**")
            self.min_current.set_min_current()
            log.debug("**Sollstrom setzen**")
            common.reset_current_to_target_current()
            self.additional_current.set_additional_current([0, 8])
            counter.limit_raw_power_left_to_surplus(self.evu_counter.calc_surplus())
            self.surplus_controlled.check_switch_on()
            if self.evu_counter.data["set"]["surplus_power_left"] > 0:
                log.debug("**PV-geführten Strom setzen**")
                common.reset_current_to_target_current()
                self.surplus_controlled.set_required_current_to_max()
                self.surplus_controlled.set_surplus_current([6, 12])
            else:
                log.debug("**Keine Leistung für PV-geführtes Laden übrig.**")
            self.no_current.set_no_current()
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
                    control_parameter = charging_ev.data.control_parameter
                    pv_auto_switch = (control_parameter.chargemode == Chargemode.PV_CHARGING and
                                      data.data.general_data.get_phases_chargemode(Chargemode.PV_CHARGING.value) == 0)
                    scheduled_auto_switch = (
                        control_parameter.chargemode == Chargemode.SCHEDULED_CHARGING and
                        control_parameter.submode == Chargemode.PV_CHARGING and
                        data.data.general_data.get_phases_chargemode(Chargemode.SCHEDULED_CHARGING.value) == 0)
                    if (cp.cp_ev_support_phase_switch() and cp.data.get.charge_state and
                            (pv_auto_switch or scheduled_auto_switch) and
                            control_parameter.timestamp_perform_phase_switch is None):
                        # Gibt die Stromstärke und Phasen zurück, mit denen nach der Umschaltung geladen werden
                        # soll. Falls keine Umschaltung erforderlich ist, werden Strom und Phasen, die übergeben
                        # wurden, wieder zurückgegeben.
                        log.debug(f"Ladepunkt {cp.num}: Prüfen, ob Phasenumschaltung durchgeführt werden soll.")
                        phases, current, message = charging_ev.auto_phase_switch(
                            cp.num,
                            cp.data.get.currents,
                            cp.data.get.power,
                            cp.template.data.max_current_single_phase)
                        if message is not None:
                            cp.data.get.state_str = message
                        # Nachdem im Automatikmodus die Anzahl Phasen bekannt ist, Einhaltung des Maximalstroms
                        # prüfen.
                        required_current = charging_ev.check_min_max_current(current, control_parameter.phases)
                        charging_ev.data.control_parameter.required_current = required_current
                        Pub().pub("openWB/set/vehicle/"+str(charging_ev.num) +
                                  "/control_parameter/required_current", required_current)
                        charging_ev.data.control_parameter.phases = phases
                        Pub().pub("openWB/set/vehicle/"+str(charging_ev.num) +
                                  "/control_parameter/phases", phases)
                        cp.set_required_currents(required_current)
            except Exception:
                log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.num}")
