import logging
from control import data
from control.chargemode import Chargemode
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE
from control.algorithm.filter_chargepoints import get_chargepoints_with_required_current_by_chargemode
from helpermodules.phase_handling import voltages_mean

from control.limiting_value import LoadmanagementLimit
from control.loadmanagement import Loadmanagement

from control.chargepoint.chargepoint import Chargepoint
import control.algorithm.common as common
from typing import List


log = logging.getLogger(__name__)


class Bidi:
    def __init__(self):
        pass

    def set_bidi(self):
        grid_counter = data.data.counter_all_data.get_evu_counter()
        log.debug(f"Nullpunktanpassung {grid_counter.data.set.surplus_power_left}W")
        for mode_tuple in CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE:
            preferenced_cps = get_chargepoints_with_required_current_by_chargemode(mode_tuple)
            if preferenced_cps:
                log.info(
                    f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {grid_counter.num}")

                while len(preferenced_cps):
                    cp = preferenced_cps[0]
                    counts = self.get_counts(cp)

                    cp.data.set.target_current = 0

                    missing_currents = self.get_missing_currents(preferenced_cps, grid_counter)
                    log.debug(f"Bidi-LP{cp.num}: missing currents {missing_currents}A")

                    counters = data.data.counter_all_data.get_counters_to_check(cp.num)
                    for counter in counters:
                        available_currents, limit = Loadmanagement().get_available_currents_bidi(
                            missing_currents, voltages_mean(cp.data.get.voltages), data.data.counter_data[counter])

                        if limit.limiting_value is not None:
                            cp.data.control_parameter.limit = limit

                        available_for_cp = common.available_current_for_cp(
                            cp, counts, available_currents, missing_currents, bidi_mode=True)

                        # Der neue Strom darf nicht höher als der bisher gesetzte Strom sein
                        current = common.get_current_to_set(
                            cp.data.set.current, available_for_cp, cp.data.set.target_current)

                        cp.data.set.current = current
                        log.info(f"LP{cp.num}: Stromstärke {current}A")

                        # Ausgabe LIMIT-MSG
                        self._set_loadmangement_message(current, limit, cp)

                    common.set_current_counterdiff(cp.data.set.target_current, current, cp, surplus=True)

                    preferenced_cps.pop(0)

    def _set_loadmangement_message(self,
                                   current: float,
                                   limit: LoadmanagementLimit,
                                   chargepoint: Chargepoint) -> None:
        # Strom muss an diesem Zähler geändert werden
        log.debug(
            f"current {current} target {chargepoint.data.set.target_current} set current {chargepoint.data.set.current}"
            f" required currents {chargepoint.data.control_parameter.required_currents}")
        required_currents = chargepoint.data.control_parameter.required_currents
        required_current = min(required_currents) if current < 0 else max(required_currents)
        if (limit.message and
                # Strom erreicht nicht die vorgegebene Stromstärke
                round(current, 2) != round(required_current, 2)):
            if current == 0:
                chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen/entladen werden"
                                              f"{limit.message}")
            elif current < 0:
                chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke entladen werden"
                                              f"{limit.message}")
            else:
                chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                              f"{limit.message}")

    def get_counts(self, chargepoint: Chargepoint) -> List[int]:

        counts = [0]*3
        required_currents = chargepoint.data.control_parameter.required_currents
        for i in range(3):
            if required_currents[i] != 0:
                counts[i] += 1
        return counts

    def get_missing_currents(self, preferenced_cps: List[Chargepoint], grid_counter) -> List[float]:
        cp = preferenced_cps[0]
        missing_currents = [0, 0, 0]
        if cp.data.control_parameter.chargemode == Chargemode.INSTANT_CHARGING:
            # Entladen im Instant-Charging-Modus
            if cp.data.set.charging_ev_data.data.get.soc is None:
                raise ValueError(f"LP{cp.num}: Auto-Bat SoC unbekannt, daher keine Entladung möglich.")
            if cp.data.set.charging_ev_data.data.get.soc > 0:
                # Auto-bat ist nicht leer

                dc_current = cp.data.set.charging_ev_data.charge_template.data.chargemode.instant_charging.dc_current
                if dc_current < 0:
                    # Phasen in use berücksichtigen
                    missing_currents = [dc_current for i in range(0, cp.data.get.phases_in_use)]
                    missing_currents += [0] * (3 - len(missing_currents))

                    for index in range(0, 3):
                        missing_currents[index] = cp.check_min_max_current(
                            missing_currents[index], cp.data.get.phases_in_use)

        else:
            # Default Nullpunktanpassung
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

        return missing_currents
