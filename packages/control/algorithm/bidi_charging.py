import logging
from control import data
from control.chargemode import Chargemode
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE
from control.algorithm.filter_chargepoints import get_chargepoints_with_required_current_by_chargemode
from helpermodules.phase_handling import voltages_mean

from control.limiting_value import LoadmanagementLimit
from control.loadmanagement import Loadmanagement
from control.algorithm import common

from control.chargepoint.chargepoint import Chargepoint
from typing import Iterable, List, Optional, Tuple


from helpermodules.phase_handling import voltages_mean


log = logging.getLogger(__name__)


class Bidi:
    def __init__(self):
        pass

    def set_bidi(self):
        grid_counter = data.data.counter_all_data.get_evu_counter()
        log.debug(f"Nullpunktanpassung {grid_counter.data.set.surplus_power_left}W")
        zero_point_adjustment = grid_counter
        for mode_tuple in CONSIDERED_CHARGE_MODES_BIDI_DISCHARGE:
            preferenced_cps = get_chargepoints_with_required_current_by_chargemode(mode_tuple)
            if preferenced_cps:
                log.info(
                    f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}, Zähler {grid_counter.num}")

                # todo: counts richtig einbinden...
                counts = [1, 1, 1]
                while len(preferenced_cps):
                    cp = preferenced_cps[0]

                    cp.data.set.target_current = 0
                    counters = data.data.counter_all_data.get_counters_to_check(cp.num)

                    missing_currents = self.get_missing_currents(preferenced_cps, grid_counter)
                    log.debug(f"############_LP{cp.num}: missing currents {missing_currents}A")

                    # Hier Limit per Loadmanagement
                    # -> geht alle Counter über dem cp durch und limit auf den niedrigsten erlaubten Wert
                    log.debug(f"ÜBERSCHUSS VOR COUNTER_LIMIT{grid_counter.data.set.surplus_power_left}")
                    for counter in counters:
                        available_currents, limit = Loadmanagement().get_available_currents_bidi(
                            missing_currents, voltages_mean(cp.data.get.voltages), data.data.counter_data[counter], cp)

                        if limit.limiting_value is not None:
                            cp.data.control_parameter.limit = limit

                        available_for_cp = self.available_current_for_cp(
                            cp, counts, available_currents, missing_currents)

                        # Hier sagt man dann mann will nur das minimum setzen,
                        # -> wegen übergeordneten Zählern
                        current = self.get_current_to_set(
                            cp.data.set.current, available_for_cp, cp.data.set.target_current)

                        log.debug(f"AV for CP {cp.num}: {available_for_cp} current {current}A")

                        cp.data.set.current = current
                        log.info(f"LP{cp.num}: Stromstärke {current}A")

                        log.debug(f"cp {cp.num} available currents {available_currents} missing currents "
                                  f"{missing_currents} limit {limit.message} -----counter_{counter}"
                                  f"CURRENT {current}A")

                    log.debug(f"_After_check________LP{cp.num}: available currents {current}A")

                    x = [current, current, current]

                    grid_counter.update_surplus_values_left(
                        x, voltages_mean(cp.data.get.voltages))

                    preferenced_cps.pop(0)

    def _set_loadmangement_message(self,
                                   current: float,
                                   limit: LoadmanagementLimit,
                                   chargepoint: Chargepoint) -> None:
        # Strom muss an diesem Zähler geändert werden
        log.debug(
            f"current {current} target {chargepoint.data.set.target_current} set current {chargepoint.data.set.current}"
            f" required currents {chargepoint.data.control_parameter.required_currents}")
        if (current != max(chargepoint.data.set.target_current, chargepoint.data.set.current or 0) and
                # Strom erreicht nicht die vorgegebene Stromstärke
                round(current, 2) != round(max(
                    chargepoint.data.control_parameter.required_currents), 2)):
            chargepoint.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                          f"{limit.message}")

    def get_counts(self, preferenced_chargepoints: List[Chargepoint]) -> List[int]:

        counts = [0]*3
        for chargepoint in preferenced_chargepoints:
            required_currents = chargepoint.data.control_parameter.required_currents
            for i in range(0, 3):
                if required_currents[i] != 0:
                    counts[i] += 1
        return counts

    def get_missing_currents(self, preferenced_cps: List[Chargepoint], grid_counter) -> List[float]:

        cp = preferenced_cps[0]
        missing_currents = [0, 0, 0]
        if cp.data.control_parameter.chargemode == Chargemode.INSTANT_CHARGING:
            log.debug(f"ÜBERSCHUSS_ALL für LP{cp.num}: {grid_counter.data.set.surplus_power_left }W")
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
            log.debug(f"ÜBERSCHUSS_ALL für LP{cp.num}: {grid_counter.data.set.surplus_power_left }W")
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

    def get_current_to_set(self, set_current: float, diff: float, prev_current: float) -> float:
        """Der neue Strom darf nicht höher als der in dieser Stufe bisher gesetzter sein, um das LM der untergeordneten
        Zähler nicht zu untergraben. Der Vergleich muss positiv sein, wenn zum ersten Mal auf dieser Stufe ein Strom gesetzt
        wird."""
        new_current = prev_current + diff
        if set_current is not None:
            if diff < 0:
                if new_current < set_current:
                    log.debug("Neuer Soll-Strom darf beim Entladen nicht niedriger als bisher gesetzter sein: "
                              f"bisher {set_current}A, neuer {new_current}")
                    return set_current
            else:
                if new_current > set_current:
                    log.debug("BIDI_Neuer Soll-Strom darf nicht höher als bisher gesetzter sein: "
                              f"bisher {set_current}A, neuer {new_current}")
                    return set_current
        return new_current

    def available_current_for_cp(self, chargepoint: Chargepoint,
                                 counts: List[int],
                                 available_currents: List[float],
                                 missing_currents: List[float]) -> float:
        control_parameter = chargepoint.data.control_parameter
        missing_current_cp = control_parameter.required_current - chargepoint.data.set.target_current
        is_discharge = missing_current_cp < 0
        available_current = float("-inf") if is_discharge else float("inf")
        for i in range(0, 3):
            if control_parameter.required_currents[i] == 0:
                continue
            if counts[i] <= 0:
                continue

            phase_available_current = available_currents[i] / counts[i]
            if is_discharge:
                available_current = max(
                    max(missing_current_cp, phase_available_current), available_current)
            else:
                available_current = min(
                    min(missing_current_cp, phase_available_current), available_current)
        if available_current in [float("inf"), float("-inf")]:
            available_current = missing_current_cp
        return available_current

    def set_current_counterdiff(self,
                                diff_current: float,
                                current: float,
                                chargepoint: Chargepoint,
                                surplus: bool = False) -> None:
        required_currents = chargepoint.data.control_parameter.required_currents
        # considered_current = consider_less_charging_chargepoint_in_loadmanagement(
        #    chargepoint, current)
        # gar nicht ladende Autos?
        diff = diff_current
        diffs = [diff if required_currents[i] != 0 else 0 for i in range(3)]
        if max(diffs) > 0:
            counters = data.data.counter_all_data.get_counters_to_check(chargepoint.num)
            for counter in counters:
                if surplus:
                    data.data.counter_data[counter].update_surplus_values_left(
                        diffs,
                        voltages_mean(chargepoint.data.get.voltages))
                else:
                    data.data.counter_data[counter].update_values_left(
                        diffs,
                        voltages_mean(chargepoint.data.get.voltages))
            data.data.io_actions.dimming_set_import_power_left({"type": "cp", "id": chargepoint.num}, sum(diffs)*230)

        chargepoint.data.set.current = current
        log.info(f"LP{chargepoint.num}: Stromstärke {current}A")
