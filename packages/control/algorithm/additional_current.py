import logging
from typing import List

from control.algorithm import common
from control.loadmanagement import LimitingValue, Loadmanagement
from control.counter import Counter
from control.chargepoint import Chargepoint
from control.algorithm.filter_chargepoints import (get_chargepoints_by_mode, get_chargepoints_by_mode_and_counter,
                                                   get_preferenced_chargepoint_charging)
from modules.common.utils.component_parser import get_component_name_by_id

log = logging.getLogger(__name__)


class AdditionalCurrent:
    def __init__(self) -> None:
        pass

    def set_additional_current(self, mode_range: List[int]) -> None:
        self._reset_current()
        for mode_tuple, counter in common.mode_and_counter_generator(mode_range):
            preferenced_chargepoints, preferenced_cps_without_set_current = get_preferenced_chargepoint_charging(
                get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}"))
            if preferenced_chargepoints:
                common.update_raw_data(preferenced_chargepoints)
                log.debug(f"Mode-Tuple {mode_tuple}, Zähler {counter.num}")
                num_of_cp = len(preferenced_chargepoints)
                for i in range(num_of_cp):
                    cp = preferenced_chargepoints[0]
                    missing_currents, counts = common.get_missing_currents_left(preferenced_chargepoints)
                    available_currents, limit = Loadmanagement().get_available_currents(missing_currents, counter)
                    available_for_cp = common.available_current_for_cp(cp, counts, available_currents)
                    current = common.get_current_to_set(
                        cp.data.set.current, available_for_cp, cp.data.set.target_current)
                    self._set_loadmangement_message(current, limit, cp, counter)
                    common.set_current_counterdiff(
                        current - cp.data.set.charging_ev_data.ev_template.data.min_current,
                        current,
                        cp)
                    preferenced_chargepoints.pop(0)
            if preferenced_cps_without_set_current:
                for cp in preferenced_cps_without_set_current:
                    cp.data.set.current = cp.data.set.target_current

    # tested
    def _set_loadmangement_message(self,
                                   current: float,
                                   limit: LimitingValue,
                                   chargepoint: Chargepoint,
                                   counter: Counter) -> None:
        # Strom muss an diesem Zähler geändert werden
        if (current != max(chargepoint.data.set.target_current, chargepoint.data.set.current) and
                # Strom erreicht nicht die vorgegebene Stromstärke
                current != max(
                    chargepoint.data.set.charging_ev_data.data.control_parameter.required_currents)):
            chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                          f"{limit.value.format(get_component_name_by_id(counter.num))}")

    def _reset_current(self) -> None:
        for mode in common.CHARGEMODES[0:8]:
            for cp in get_chargepoints_by_mode(mode):
                cp.data.set.current = 0
