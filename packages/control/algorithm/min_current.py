import logging

from control import data
from control.algorithm import common
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_MIN_CURRENT, CONSIDERED_CHARGE_MODES_PV_ONLY
from control.chargepoint.chargepoint_state import ChargepointState
from control.loadmanagement import Loadmanagement
from control.algorithm.filter_chargepoints import get_chargepoints_by_mode_and_counter_and_lm_prio

log = logging.getLogger(__name__)


class MinCurrent:

    def __init__(self) -> None:
        pass

    def set_min_current(self, cp_prio_group) -> None:
        log.info("**Mindestrom setzen**")
        common.reset_current_to_target_current(cp_prio_group)
        for counter in common.counter_generator():
            preferenced_chargepoints = get_chargepoints_by_mode_and_counter_and_lm_prio(
                CONSIDERED_CHARGE_MODES_MIN_CURRENT,
                f"counter{counter.num}",
                cp_prio_group)
            if preferenced_chargepoints:
                log.info(f"Zähler {counter.num}, Verbraucher {preferenced_chargepoints}")
                common.update_raw_data(preferenced_chargepoints, diff_to_zero=True)
                while len(preferenced_chargepoints):
                    cp = preferenced_chargepoints[0]
                    missing_currents, counts = common.get_min_current(cp)
                    if max(missing_currents) > 0:
                        available_currents, limit = Loadmanagement().get_available_currents(
                            missing_currents, counter, cp)
                        cp.data.control_parameter.limit = limit
                        available_for_cp = common.available_current_for_cp(
                            cp, counts, available_currents, missing_currents)
                        current = common.get_current_to_set(
                            cp.data.set.current, available_for_cp, cp.data.set.target_current)
                        if current < cp.data.control_parameter.min_current:
                            common.set_current_counterdiff(-(cp.data.set.current or 0), 0, cp)
                            if limit:
                                cp.set_state_and_log(
                                    f"Ladung kann nicht gestartet werden{limit.message}")
                        else:
                            common.set_current_counterdiff(
                                cp.data.set.target_current,
                                cp.data.control_parameter.min_current,
                                cp)
                    else:
                        if (cp.data.control_parameter.chargemode,
                                cp.data.control_parameter.submode) in CONSIDERED_CHARGE_MODES_PV_ONLY:
                            try:
                                if (cp.data.control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED or
                                        cp.data.control_parameter.state == ChargepointState.SWITCH_ON_DELAY):
                                    data.data.counter_all_data.get_evu_counter().switch_on_threshold_reached(cp)
                            except Exception:
                                log.exception(f"Fehler in der PV-gesteuerten Ladung bei {cp.num}")
                        cp.data.set.current = 0
                    preferenced_chargepoints.pop(0)
