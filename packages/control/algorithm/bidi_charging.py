import logging
from control import data
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE
from control.algorithm.filter_chargepoints import get_loadmanagement_prios
from helpermodules.phase_handling import voltages_mean

log = logging.getLogger(__name__)


class Bidi:
    def __init__(self):
        pass

    def set_bidi(self):
        grid_counter = data.data.counter_all_data.get_evu_counter()
        log.debug(f"Nullpunktanpassung {grid_counter.data.set.surplus_power_left}W")
        zero_point_adjustment = grid_counter
        preferenced_cps = get_loadmanagement_prios(CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE)
        if preferenced_cps:
            log.info(f"Verbraucher {preferenced_cps}")
            while len(preferenced_cps):
                cp = preferenced_cps[0]
                zero_point_adjustment = grid_counter.data.set.surplus_power_left / len(preferenced_cps)
                log.debug(f"Nullpunktanpassung für LP{cp.num}: verbleibende Leistung {zero_point_adjustment}W")
                missing_currents = [zero_point_adjustment / cp.data.get.phases_in_use /
                                    230 for i in range(0, cp.data.get.phases_in_use)]
                missing_currents += [0] * (3 - len(missing_currents))
                if zero_point_adjustment > 0:
                    if cp.data.set.charging_ev_data.charge_template.bidi_charging_allowed(
                            cp.data.control_parameter.current_plan, cp.data.set.charging_ev_data.data.get.soc):
                        for index in range(0, 3):
                            missing_currents[index] = min(cp.data.control_parameter.required_current,
                                                          missing_currents[index])
                    else:
                        log.info(f"LP{cp.num}: Nur bidirektional entladen erlaubt, da SoC-Limit erreicht.")
                        missing_currents = [0, 0, 0]
                else:
                    for index in range(0, 3):
                        missing_currents[index] = cp.check_min_max_current(missing_currents[index],
                                                                           cp.data.get.phases_in_use)
                grid_counter.update_surplus_values_left(missing_currents, voltages_mean(cp.data.get.voltages))
                cp.data.set.current = missing_currents[0]
                log.info(f"LP{cp.num}: Stromstärke {missing_currents}A")
                preferenced_cps.pop(0)
