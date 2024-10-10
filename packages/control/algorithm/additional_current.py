import logging

from control.algorithm import common
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT
from control.loadmanagement import LimitingValue, Loadmanagement
from control.counter import Counter
from control.chargepoint.chargepoint import Chargepoint
from control.algorithm.filter_chargepoints import (get_chargepoints_by_mode_and_counter,
                                                   get_preferenced_chargepoint_charging)
from modules.common.utils.component_parser import get_component_name_by_id

log = logging.getLogger(__name__)


class AdditionalCurrent:

    def __init__(self) -> None:
        pass

    def set_additional_current(self) -> None:
        common.reset_current_by_chargemode(CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT)
        for mode_tuple, counter in common.mode_and_counter_generator(CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT):
            preferenced_chargepoints, preferenced_cps_without_set_current = get_preferenced_chargepoint_charging(
                get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}"))
            if preferenced_chargepoints:
                common.update_raw_data(preferenced_chargepoints)
                log.info(f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {counter.num}")
                while len(preferenced_chargepoints):
                    cp = preferenced_chargepoints[0]
                    missing_currents, counts = common.get_missing_currents_left(preferenced_chargepoints)
                    available_currents, limit = Loadmanagement().get_available_currents(missing_currents, counter)
                    log.debug(f"cp {cp.num} available currents {available_currents} missing currents "
                              f"{missing_currents} limit {limit}")
                    cp.data.control_parameter.limit = limit
                    available_for_cp = common.available_current_for_cp(cp, counts, available_currents, missing_currents)
                    current = common.get_current_to_set(
                        cp.data.set.current, available_for_cp, cp.data.set.target_current)
                    self._set_loadmangement_message(current, limit, cp, counter)
                    common.set_current_counterdiff(
                        cp.data.control_parameter.min_current,
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
        log.debug(
            f"current {current} target {chargepoint.data.set.target_current} set current {chargepoint.data.set.current}"
            f" required currents {chargepoint.data.control_parameter.required_currents}")
        if (current != max(chargepoint.data.set.target_current, chargepoint.data.set.current or 0) and
                # Strom erreicht nicht die vorgegebene Stromstärke
                round(current, 2) != round(max(
                    chargepoint.data.control_parameter.required_currents), 2)):
            chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                          f"{limit.value.format(get_component_name_by_id(counter.num))}")
