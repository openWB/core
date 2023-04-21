import logging

from control.algorithm import common
from control.loadmanagement import Loadmanagement
from control.algorithm.filter_chargepoints import get_chargepoints_by_mode_and_counter

log = logging.getLogger(__name__)


class MinCurrent:
    def __init__(self) -> None:
        pass

    def set_min_current(self) -> None:
        for mode_tuple, counter in common.mode_and_counter_generator():
            preferenced_chargepoints = get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}")
            if preferenced_chargepoints:
                log.info(f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {counter.num}")
                common.update_raw_data(preferenced_chargepoints, diff_to_zero=True)
                while len(preferenced_chargepoints):
                    cp = preferenced_chargepoints[0]
                    missing_currents, counts = common.get_min_current(cp)
                    if max(missing_currents) > 0:
                        available_currents, limit = Loadmanagement().get_available_currents(missing_currents, counter)
                        available_for_cp = common.available_current_for_cp(
                            cp, counts, available_currents, missing_currents)
                        if common.consider_not_charging_chargepoint_in_loadmanagement(cp):
                            cp.data.set.current = cp.data.set.charging_ev_data.ev_template.data.min_current
                            log.debug(
                                f"LP{cp.num}: Stromstärke {cp.data.set.charging_ev_data.ev_template.data.min_current}"
                                "A. Zuteilung ohne Berücksichtigung im Lastmanagement, da kein Ladestart zu erwarten "
                                "ist und Reserve für nicht-ladende inaktiv.")
                        else:
                            if available_for_cp < cp.data.set.charging_ev_data.ev_template.data.min_current:
                                common.set_current_counterdiff(-cp.data.set.current, 0, cp)
                                cp.set_state_and_log(
                                    f"Ladung kann nicht gestartet werden{limit.value.format(counter.num)}")
                            else:
                                common.set_current_counterdiff(
                                    (cp.data.set.charging_ev_data.ev_template.data.min_current
                                     - cp.data.set.target_current),
                                    cp.data.set.charging_ev_data.ev_template.data.min_current,
                                    cp)
                    preferenced_chargepoints.pop(0)
