import logging

from control.algorithm import common
from control.loadmanagement import Loadmanagement
from control.algorithm.filter_chargepoints import get_chargepoints_by_mode_and_counter

log = logging.getLogger(__name__)


class MinCurrent:
    CONSIDERED_CHARGE_MODES = common.CHARGEMODES[0:-1]

    def __init__(self) -> None:
        pass

    def set_min_current(self) -> None:
        for mode_tuple, counter in common.mode_and_counter_generator(self.CONSIDERED_CHARGE_MODES):
            preferenced_chargepoints = get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}")
            if preferenced_chargepoints:
                log.info(f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {counter.num}")
                common.update_raw_data(preferenced_chargepoints, diff_to_zero=True)
                while len(preferenced_chargepoints):
                    cp = preferenced_chargepoints[0]
                    missing_currents, counts = common.get_min_current(cp)
                    if max(missing_currents) > 0:
                        available_currents, limit = Loadmanagement().get_available_currents(missing_currents, counter)
                        cp.data.control_parameter.limit = limit
                        available_for_cp = common.available_current_for_cp(
                            cp, counts, available_currents, missing_currents)
                        current = common.get_current_to_set(
                            cp.data.set.current, available_for_cp, cp.data.set.target_current)
                        if current < cp.data.control_parameter.min_current:
                            common.set_current_counterdiff(-(cp.data.set.current or 0), 0, cp)
                            if limit:
                                cp.set_state_and_log(
                                    f"Ladung kann nicht gestartet werden{limit.value.format(counter.num)}")
                        else:
                            common.set_current_counterdiff(
                                cp.data.set.target_current,
                                cp.data.control_parameter.min_current,
                                cp)
                    else:
                        cp.data.set.current = 0
                    preferenced_chargepoints.pop(0)
