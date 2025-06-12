import logging
from control import data
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE
from control.algorithm.filter_chargepoints import get_chargepoints_by_mode

log = logging.getLogger(__name__)


class Bidi:
    def __init__(self):
        pass

    def set_bidi(self):
        grid_counter = data.data.counter_all_data.get_evu_counter()
        zero_point_adjustment = grid_counter
        if grid_counter.data.set.surplus_power_left < 0:
            for mode_tuple in CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE:
                preferenced_cps = get_chargepoints_by_mode(mode_tuple)
                if preferenced_cps:
                    log.info(
                        f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {grid_counter.num}")
                    while len(preferenced_cps):
                        cp = preferenced_cps[0]
                        zero_point_adjustment = grid_counter.data.set.surplus_power_left / len(preferenced_cps)
                        log.debug(f"Nullpunktanpassung für LP{cp.num}: {zero_point_adjustment}W")
                        missing_currents = [0]*3
                        missing_currents = [zero_point_adjustment / cp.data.get.phases_in_use /
                                            230 for i in range(0, cp.data.get.phases_in_use)]
                        grid_counter.update_surplus_values_left(missing_currents, cp.data.get.voltages)
                        cp.data.set.current = missing_currents[0]
                        log.info(f"LP{cp.num}: Stromstärke {missing_currents}A")
                        preferenced_cps.pop(0)
