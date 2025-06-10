import logging
from control import data
from control.algorithm import common
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_BIDI
from control.algorithm.filter_chargepoints import (get_chargepoints_by_mode_and_counter,
                                                   get_preferenced_chargepoint_charging)
from control.algorithm.surplus_controlled import limit_adjust_current
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.limiting_value import LimitingValue
from control.loadmanagement import Loadmanagement
from modules.common.utils.component_parser import get_component_name_by_id

log = logging.getLogger(__name__)


class Bidi:
    def __init__(self):
        pass

    def set_bidi(self):
        grid_counter = data.data.counter_all_data.get_evu_counter()
        for mode_tuple, counter in common.mode_and_counter_generator(CONSIDERED_CHARGE_MODES_BIDI):
            preferenced_cps_without_set_current = get_preferenced_chargepoint_charging(
                get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}"))[1]
            if preferenced_cps_without_set_current:
                log.info(f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {counter.num}")
                common.update_raw_data(preferenced_cps_without_set_current, surplus=True)
                while len(preferenced_cps_without_set_current):
                    cp = preferenced_cps_without_set_current[0]
                    missing_currents = [(grid_counter.data.config.max_total_power -
                                         grid_counter.data.set.raw_power_left) /
                                        cp.data.get.phases_in_use for i in range(0, cp.data.get.phases_in_use)]
                    available_currents, limit = Loadmanagement().get_available_currents_surplus(missing_currents,
                                                                                                counter)
                    cp.data.control_parameter.limit = limit
                    available_for_cp = common.available_current_for_cp(
                        cp, cp.data.get.phases_in_use, available_currents, missing_currents)

                    current = common.get_current_to_set(
                        cp.data.set.current, available_for_cp, cp.data.set.target_current)
                    self._set_loadmangement_message(current, limit, cp, counter)
                    limited_current = limit_adjust_current(cp, current)
                    common.set_current_counterdiff(
                        cp.data.control_parameter.min_current,
                        limited_current,
                        cp,
                        surplus=True)
                    preferenced_cps_without_set_current.pop(0)

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
