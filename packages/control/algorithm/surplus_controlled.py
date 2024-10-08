import logging
from typing import List, Optional, Tuple

from control import data
from control.algorithm import common
from control.loadmanagement import LimitingValue, Loadmanagement
from control.counter import Counter
from control.chargepoint.chargepoint import Chargepoint
from control.algorithm.filter_chargepoints import (get_chargepoints_by_mode, get_chargepoints_by_mode_and_counter,
                                                   get_preferenced_chargepoint_charging)
from control.chargepoint.chargepoint_state import ChargepointState, CHARGING_STATES
from modules.common.utils.component_parser import get_component_name_by_id

log = logging.getLogger(__name__)

CONSIDERED_CHARGE_MODES = common.CHARGEMODES[0:2] + common.CHARGEMODES[6:12]
CONSIDERED_CHARGE_MODES_PV = common.CHARGEMODES[8:12]


class SurplusControlled:

    def __init__(self) -> None:
        pass

    def set_surplus_current(self) -> None:
        common.reset_current_by_chargemode(CONSIDERED_CHARGE_MODES)
        for mode_tuple, counter in common.mode_and_counter_generator(CONSIDERED_CHARGE_MODES):
            preferenced_chargepoints, preferenced_cps_without_set_current = get_preferenced_chargepoint_charging(
                get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}"))
            cp_with_feed_in, cp_without_feed_in = self.filter_by_feed_in_limit(preferenced_chargepoints)
            if cp_without_feed_in:
                self._set(cp_without_feed_in, 0, mode_tuple, counter)
            feed_in_yield = data.data.general_data.data.chargemode_config.pv_charging.feed_in_yield
            if cp_with_feed_in:
                self._set(cp_with_feed_in, feed_in_yield, mode_tuple, counter)
            if preferenced_cps_without_set_current:
                for cp in preferenced_cps_without_set_current:
                    cp.data.set.current = cp.data.set.target_current

    def _set(self,
             chargepoints: List[Chargepoint],
             feed_in_yield: Optional[int],
             mode_tuple: Tuple[Optional[str], str, bool],
             counter: Counter) -> None:
        log.info(f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {counter.num}")
        common.update_raw_data(chargepoints, surplus=True)
        while len(chargepoints):
            cp = chargepoints[0]
            missing_currents, counts = common.get_missing_currents_left(chargepoints)
            available_currents, limit = Loadmanagement().get_available_currents_surplus(missing_currents,
                                                                                        counter,
                                                                                        feed_in_yield)
            cp.data.control_parameter.limit = limit
            available_for_cp = common.available_current_for_cp(cp, counts, available_currents, missing_currents)
            current = common.get_current_to_set(cp.data.set.current, available_for_cp, cp.data.set.target_current)
            self._set_loadmangement_message(current, limit, cp, counter)
            limited_current = self._limit_adjust_current(cp, current)
            limited_current = self._fix_deviating_evse_current(limited_current, cp)
            common.set_current_counterdiff(
                cp.data.control_parameter.min_current,
                limited_current,
                cp,
                surplus=True)
            chargepoints.pop(0)

    def _set_loadmangement_message(self,
                                   current: float,
                                   limit: LimitingValue,
                                   chargepoint: Chargepoint,
                                   counter: Counter) -> None:
        # Strom muss an diesem Zähler geändert werden
        if (current != chargepoint.data.set.current and
                # Strom erreicht nicht die vorgegebene Stromstärke
                current != max(chargepoint.data.control_parameter.required_currents) and
                # im PV-Laden wird der Strom immer durch die Leistung begrenzt
                limit != LimitingValue.POWER):
            chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                          f"{limit.value.format(get_component_name_by_id(counter.num))}")

    # tested
    def filter_by_feed_in_limit(self, chargepoints: List[Chargepoint]) -> Tuple[List[Chargepoint], List[Chargepoint]]:
        cp_with_feed_in = list(filter(lambda cp: cp.data.set.charging_ev_data.charge_template.data.chargemode.
                                      pv_charging.feed_in_limit is True, chargepoints))
        cp_without_feed_in = list(filter(lambda cp: cp.data.set.charging_ev_data.charge_template.data.chargemode.
                                         pv_charging.feed_in_limit is False, chargepoints))
        return cp_with_feed_in, cp_without_feed_in

    # tested
    def _limit_adjust_current(self, chargepoint: Chargepoint, new_current: float) -> float:
        MAX_CURRENT = 5
        msg = None
        nominal_difference = chargepoint.data.set.charging_ev_data.ev_template.data.nominal_difference
        if chargepoint.data.set.charging_ev_data.chargemode_changed:
            return new_current
        else:
            # Um max. +/- 5A pro Zyklus regeln
            if (-MAX_CURRENT-nominal_difference
                    < new_current - max(chargepoint.data.get.currents)
                    < MAX_CURRENT+nominal_difference):
                current = new_current
            else:
                if new_current < max(chargepoint.data.get.currents):
                    current = max(chargepoint.data.get.currents) - MAX_CURRENT
                    msg = "Es darf um max 5A unter den aktuell genutzten Strom geregelt werden."

                else:
                    current = max(chargepoint.data.get.currents) + MAX_CURRENT
                    msg = "Es darf um max 5A über den aktuell genutzten Strom geregelt werden."
            chargepoint.set_state_and_log(msg)
            return max(current, chargepoint.data.control_parameter.min_current)

    def _fix_deviating_evse_current(self, limited_current, chargepoint: Chargepoint) -> float:
        """Wenn Autos nicht die volle Ladeleistung nutzen, wird unnötig eingespeist. Dann kann um den noch nicht
        genutzten Soll-Strom hochgeregelt werden. Wenn Fahrzeuge entgegen der Norm mehr Ladeleistung beziehen, als
        freigegeben, wird entsprechend weniger freigegeben, da sonst uU die untere Grenze für die Abschaltschwelle
        nicht erreicht wird."""
        evse_current = chargepoint.data.get.evse_current
        if evse_current:
            formatted_evse_current = evse_current if evse_current < 32 else evse_current / 100
            current_with_offset = limited_current + formatted_evse_current - max(chargepoint.data.get.currents)
            current = min(current_with_offset, chargepoint.data.control_parameter.required_current)
            if current != limited_current:
                log.debug(f"Ungenutzten Soll-Strom aufschlagen ergibt {current}A.")
            return current
        else:
            return limited_current

    def check_submode_pv_charging(self) -> None:
        evu_counter = data.data.counter_all_data.get_evu_counter()

        for cp in get_chargepoints_pv_charging():
            def phase_switch_necessary() -> bool:
                return cp.cp_ev_chargemode_support_phase_switch() and cp.data.get.phases_in_use != 1
            control_parameter = cp.data.control_parameter
            if cp.data.set.charging_ev_data.chargemode_changed or cp.data.set.charging_ev_data.submode_changed:
                if control_parameter.state == ChargepointState.CHARGING_ALLOWED:
                    if (cp.data.set.charging_ev_data.ev_template.data.prevent_charge_stop is False and
                            phase_switch_necessary() is False):
                        threshold = evu_counter.calc_switch_off_threshold(cp)[0]
                        if evu_counter.calc_raw_surplus() - cp.data.set.required_power < threshold:
                            control_parameter.required_currents = [0]*3
                            control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
                else:
                    control_parameter.required_currents = [0]*3
            else:
                if ((control_parameter.state == ChargepointState.CHARGING_ALLOWED or
                        control_parameter.state == ChargepointState.SWITCH_OFF_DELAY) and
                        phase_switch_necessary() is False):
                    evu_counter.switch_off_check_threshold(cp)
                if control_parameter.state == ChargepointState.SWITCH_OFF_DELAY:
                    evu_counter.switch_off_check_timer(cp)
                if control_parameter.state == ChargepointState.SWITCH_ON_DELAY:
                    # Wenn charge_state False und set_current > 0, will Auto nicht laden
                    evu_counter.switch_on_timer_expired(cp)
                if control_parameter.state not in CHARGING_STATES:
                    control_parameter.required_currents = [0]*3

    def check_switch_on(self) -> None:
        for cp in get_chargepoints_pv_charging():
            if (cp.data.control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED or
                    cp.data.control_parameter.state == ChargepointState.SWITCH_ON_DELAY):
                data.data.counter_all_data.get_evu_counter().switch_on_threshold_reached(cp)

    def set_required_current_to_max(self) -> None:
        for cp in get_chargepoints_surplus_controlled():
            charging_ev_data = cp.data.set.charging_ev_data
            required_currents = cp.data.control_parameter.required_currents
            control_parameter = cp.data.control_parameter

            if control_parameter.phases == 1:
                max_current = charging_ev_data.ev_template.data.max_current_single_phase
            else:
                max_current = charging_ev_data.ev_template.data.max_current_multi_phases

            control_parameter.required_currents = [max_current if required_currents[i] != 0 else 0 for i in range(3)]
            control_parameter.required_current = max_current


def get_chargepoints_pv_charging() -> List[Chargepoint]:
    chargepoints: List[Chargepoint] = []
    for mode in CONSIDERED_CHARGE_MODES_PV:
        chargepoints.extend(get_chargepoints_by_mode(mode))
    return chargepoints


def get_chargepoints_surplus_controlled() -> List[Chargepoint]:
    chargepoints: List[Chargepoint] = []
    for mode in CONSIDERED_CHARGE_MODES:
        chargepoints.extend(get_chargepoints_by_mode(mode))
    return chargepoints
