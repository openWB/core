import logging
from typing import List, Optional, Tuple

from control import data
from control.algorithm import common
from control.loadmanagement import LimitingValue, Loadmanagement
from control.counter import Counter
from control.chargepoint import Chargepoint
from control.algorithm.filter_chargepoints import (get_chargepoints_by_mode, get_chargepoints_by_mode_and_counter,
                                                   get_preferenced_chargepoint_charging, get_chargepoints_pv_charging,
                                                   get_chargepoints_surplus_led)
from modules.common.utils.component_parser import get_component_name_by_id

log = logging.getLogger(__name__)


class SurplusLed:
    def __init__(self) -> None:
        pass

    def set_surplus_current(self, mode_range) -> None:
        self._reset_current()
        for mode_tuple, counter in common.mode_and_counter_generator(mode_range):
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
        log.debug(f"Mode-Tuple {mode_tuple}, Zähler {counter.num}")
        common.update_raw_data(chargepoints, surplus=True)
        while len(chargepoints):
            cp = chargepoints[0]
            missing_currents, counts = common.get_missing_currents_left(chargepoints)
            available_currents, limit = Loadmanagement().get_available_currents_surplus(missing_currents,
                                                                                        counter,
                                                                                        feed_in_yield)
            available_for_cp = common.available_current_for_cp(cp, counts, available_currents)
            current = common.get_current_to_set(cp.data.set.current, available_for_cp, cp.data.set.target_current)
            self._set_loadmangement_message(current, limit, cp, counter)
            limited_current = self._limit_adjust_current(cp, current)
            common.set_current_counterdiff(
                limited_current - cp.data.set.charging_ev_data.ev_template.data.min_current,
                limited_current,
                cp,
                surplus=True)
            chargepoints.pop(0)

    def _reset_current(self) -> None:
        for mode in common.CHARGEMODES[6:12]:
            for cp in get_chargepoints_by_mode(mode):
                cp.data.set.current = 0

    def _set_loadmangement_message(self,
                                   current: float,
                                   limit: LimitingValue,
                                   chargepoint: Chargepoint,
                                   counter: Counter) -> None:
        # Strom muss an diesem Zähler geändert werden
        if (current != chargepoint.data.set.current and
                # Strom erreicht nicht die vorgegebene Stromstärke
                current != max(chargepoint.data.set.charging_ev_data.data.control_parameter.required_currents) and
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
        return max(current, chargepoint.data.set.charging_ev_data.ev_template.data.min_current)

    def check_submode_pv_charging(self) -> None:
        for cp in get_chargepoints_pv_charging():
            if cp.data.set.current != 0:
                if data.data.counter_all_data.get_evu_counter().switch_off_check_timer(cp):
                    cp.data.set.charging_ev_data.data.control_parameter.required_currents = [0]*3
                else:
                    data.data.counter_all_data.get_evu_counter().switch_off_check_threshold(cp)
            else:
                # Wenn charge_state False und set_current > 0, will Auto nicht laden
                if not data.data.counter_all_data.get_evu_counter().switch_on_timer_expired(cp):
                    cp.data.set.charging_ev_data.data.control_parameter.required_currents = [0]*3

    def check_switch_on(self) -> None:
        for cp in get_chargepoints_pv_charging():
            if (cp.data.set.current == 0 and
                    cp.data.set.charging_ev_data.data.control_parameter.timestamp_switch_on_off is None and
                    cp.data.set.charging_ev_data.data.control_parameter.timestamp_perform_phase_switch is None):
                data.data.counter_all_data.get_evu_counter().switch_on_threshold_reached(cp)

    def set_required_current_to_max(self) -> None:
        for cp in get_chargepoints_surplus_led():
            charging_ev_data = cp.data.set.charging_ev_data
            required_currents = charging_ev_data.data.control_parameter.required_currents

            if charging_ev_data.data.control_parameter.phases == 1:
                charging_ev_data.data.control_parameter.required_currents = [
                    charging_ev_data.ev_template.data.max_current_one_phase if required_currents[i] != 0 else 0
                    for i in range(3)]
            else:
                charging_ev_data.data.control_parameter.required_currents = [
                    charging_ev_data.ev_template.data.max_current_multi_phases]*3
