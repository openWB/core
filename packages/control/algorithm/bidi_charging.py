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
        log.debug(f"Nullpunktanpassung {grid_counter.data.set.surplus_power_left}W")
        zero_point_adjustment = grid_counter
        for mode_tuple in CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE:
            preferenced_cps = get_chargepoints_by_mode(mode_tuple)
            if preferenced_cps:
                log.info(
                    f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {grid_counter.num}")
                while len(preferenced_cps):
                    cp = preferenced_cps[0]
                    zero_point_adjustment = grid_counter.data.set.surplus_power_left / len(preferenced_cps)
                    log.debug(f"Nullpunktanpassung für LP{cp.num}: verbleibende Leistung {zero_point_adjustment}W")
                    missing_currents = [zero_point_adjustment / cp.data.get.phases_in_use /
                                        230 for i in range(0, cp.data.get.phases_in_use)]
                    missing_currents += [0] * (3 - len(missing_currents))
                    for index in range(0,3):
                        if missing_currents[index] < 0:
                            missing_currents[index] = max(-32, missing_currents[index])
                        else:
                            missing_currents[index] = min(32, missing_currents[index])
                    grid_counter.update_surplus_values_left(missing_currents, cp.data.get.voltages)
                    cp.data.set.current = missing_currents[0]
                    log.info(f"LP{cp.num}: Stromstärke {missing_currents}A")
                    preferenced_cps.pop(0)
