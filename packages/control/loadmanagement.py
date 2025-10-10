import logging
import operator
from typing import List, Optional, Tuple

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.limiting_value import LimitingValue, LoadmanagementLimit
from modules.common.utils.component_parser import get_component_name_by_id


log = logging.getLogger(__name__)


class Loadmanagement:
    def get_available_currents(self,
                               missing_currents: List[float],
                               counter: Counter,
                               cp: Chargepoint,
                               feed_in: int = 0) -> Tuple[List[float], LoadmanagementLimit]:
        raw_currents_left = counter.data.set.raw_currents_left
        try:
            available_currents, limit = self._limit_by_dimming_via_direct_control(missing_currents, cp)

            available_currents, new_limit = self._limit_by_dimming(available_currents, cp)
            limit = new_limit if new_limit.limiting_value is not None else limit

            available_currents, new_limit = self._limit_by_ripple_control_receiver(available_currents, cp)
            limit = new_limit if new_limit.limiting_value is not None else limit
        except ValueError as e:
            available_currents = [0]*3
            limit = LoadmanagementLimit(e.args[0], e)

        available_currents, new_limit = self._limit_by_current(counter, available_currents, raw_currents_left)
        limit = new_limit if new_limit.limiting_value is not None else limit

        available_currents, new_limit = self._limit_by_power(
            counter, available_currents, cp.data.get.voltages, counter.data.set.raw_power_left, feed_in)
        limit = new_limit if new_limit.limiting_value is not None else limit

        if f"counter{counter.num}" == data.data.counter_all_data.get_evu_counter_str():
            available_currents, new_limit = self._limit_by_unbalanced_load(
                counter, available_currents, raw_currents_left,
                len([value for value in missing_currents if value != 0]))
            limit = new_limit if new_limit.limiting_value is not None else limit
        return available_currents, limit

    def get_available_currents_surplus(self,
                                       missing_currents: List[float],
                                       cp_voltages: List[float],
                                       counter: Counter,
                                       cp: Chargepoint,
                                       feed_in: int = 0) -> Tuple[List[float], LoadmanagementLimit]:
        raw_currents_left = counter.data.set.raw_currents_left
        available_currents, limit = self._limit_by_dimming_via_direct_control(missing_currents, cp)

        available_currents, new_limit = self._limit_by_ripple_control_receiver(available_currents, cp)
        limit = new_limit if new_limit.limiting_value is not None else limit

        available_currents, new_limit = self._limit_by_current(counter, available_currents, raw_currents_left)
        limit = new_limit if new_limit.limiting_value is not None else limit

        available_currents, new_limit = self._limit_by_power(
            counter, available_currents, cp_voltages, counter.data.set.surplus_power_left, feed_in)
        limit = new_limit if new_limit.limiting_value is not None else limit

        if f"counter{counter.num}" == data.data.counter_all_data.get_evu_counter_str():
            available_currents, new_limit = self._limit_by_unbalanced_load(
                counter, available_currents, raw_currents_left,
                len([value for value in missing_currents if value != 0]))
            limit = new_limit if new_limit.limiting_value is not None else limit
        return available_currents, limit

    def _limit_by_unbalanced_load(self,
                                  counter: Counter,
                                  available_currents: List[float],
                                  raw_currents_left: List[float],
                                  phases_to_use: int) -> Tuple[List[float], LoadmanagementLimit]:
        raw_currents_left_charging = list(map(operator.sub, raw_currents_left, available_currents))
        max_exceeding = counter.get_unbalanced_load_exceeding(raw_currents_left_charging)
        limit = LoadmanagementLimit(None, None)
        if max(max_exceeding) > 0:
            if phases_to_use < 3 and phases_to_use > 0:
                available_currents = list(map(operator.sub, available_currents, max_exceeding))
                log.debug(f"Schieflast {max_exceeding}A korrigieren: {available_currents}")
                limit = LoadmanagementLimit(
                    LimitingValue.UNBALANCED_LOAD.value.format(get_component_name_by_id(counter.num)),
                    LimitingValue.UNBALANCED_LOAD)
            elif phases_to_use == 3:
                log.debug("Schieflastkorrektur nicht möglich, da alle Phasen genutzt werden.")
        return available_currents, limit

    # tested
    def _limit_by_power(self,
                        counter: Counter,
                        available_currents: List[float],
                        cp_voltages: List[float],
                        raw_power_left: Optional[float],
                        feed_in: Optional[float]) -> Tuple[List[float], LoadmanagementLimit]:
        currents = available_currents.copy()
        limit = LoadmanagementLimit(None, None)
        if raw_power_left:
            if feed_in:
                raw_power_left = raw_power_left - feed_in
                log.debug(f"Verbleibende Leistung unter Berücksichtigung der Einspeisegrenze: {raw_power_left}W")
            if sum([c * v for c, v in zip(available_currents, cp_voltages)]) > raw_power_left:
                for i in range(0, 3):
                    # Am meisten belastete Phase trägt am meisten zur Leistungsreduktion bei.
                    currents[i] = available_currents[i] / sum(available_currents) * raw_power_left / cp_voltages[i]
                log.debug(f"Leistungsüberschreitung auf {raw_power_left}W korrigieren: {available_currents}")
                limit = LoadmanagementLimit(LimitingValue.POWER.value.format(get_component_name_by_id(counter.num)),
                                            LimitingValue.POWER)
        return currents, limit

    # tested
    def _limit_by_current(self,
                          counter: Counter,
                          missing_currents: List[float],
                          raw_currents_left: List[float]) -> Tuple[List[float], LoadmanagementLimit]:
        available_currents = [0.0]*3
        limit = LoadmanagementLimit(None, None)
        for i in range(0, 3):
            available_currents[i] = min(missing_currents[i], raw_currents_left[i])
        if available_currents != missing_currents:
            log.debug(f"Stromüberschreitung {missing_currents}W korrigieren: {available_currents}")
            limit = LoadmanagementLimit(LimitingValue.CURRENT.value.format(get_component_name_by_id(counter.num)),
                                        LimitingValue.CURRENT)
        return available_currents, limit

    def _limit_by_dimming_via_direct_control(self,
                                             missing_currents: List[float],
                                             cp: Chargepoint) -> Tuple[List[float], LoadmanagementLimit]:
        if data.data.io_actions.dimming_via_direct_control({"type": "cp", "id": cp.num}):
            phases = 3-missing_currents.count(0)
            current_per_phase = 4200 / 230 / phases
            available_currents = [current_per_phase -
                                  cp.data.set.target_current if c > 0 else 0 for c in missing_currents]
            log.debug(f"Dimmung per Direkt-Steuerung: {available_currents}A")
            limit = LoadmanagementLimit(LimitingValue.DIMMING_VIA_DIRECT_CONTROL.value,
                                        LimitingValue.DIMMING_VIA_DIRECT_CONTROL)
            return available_currents, limit
        else:
            return missing_currents, LoadmanagementLimit(None, None)

    def _limit_by_dimming(self,
                          available_currents: List[float],
                          cp: Chargepoint) -> Tuple[List[float], LoadmanagementLimit]:
        dimming_power_left = data.data.io_actions.dimming_get_import_power_left({"type": "cp", "id": cp.num})
        if dimming_power_left:
            if sum(available_currents)*230 > dimming_power_left:
                phases = 3-available_currents.count(0)
                overload_per_phase = (sum(available_currents) - dimming_power_left/230)/phases
                available_currents = [c - overload_per_phase if c > 0 else 0 for c in available_currents]
                log.debug(f"Reduzierung der Ströme durch die Dimmung: {available_currents}A")
                return available_currents, LoadmanagementLimit(LimitingValue.DIMMING.value, LimitingValue.DIMMING)
        return available_currents, LoadmanagementLimit(None, None)

    def _limit_by_ripple_control_receiver(self,
                                          available_currents: List[float],
                                          cp: Chargepoint) -> Tuple[List[float], LoadmanagementLimit]:
        value = data.data.io_actions.ripple_control_receiver({"type": "cp", "id": cp.num})
        if value != 1:
            phases = 3-available_currents.count(0)
            if phases > 1:
                max_current = cp.template.data.max_current_single_phase
            else:
                max_current = cp.template.data.max_current_multi_phases
            # target_current ist das Ergebnis der letzten Iteration. Die Differenz der begrenzten Anschlussleistung und
            # der Sollstrom der letzten Iteration dürfen daher nicht größer sein als der aktuell fehlende Strom.
            available_currents = [min(max_current*value - cp.data.set.target_current, c)
                                  if c > 0 else 0 for c in available_currents]
            log.debug(f"Reduzierung durch RSE-Kontakt auf {value*100}%, maximal {max_current*value}A")
            limit = LoadmanagementLimit(
                LimitingValue.RIPPLE_CONTROL_RECEIVER.value.format(value*100),
                LimitingValue.RIPPLE_CONTROL_RECEIVER)
            return available_currents, limit
        else:
            return available_currents, LoadmanagementLimit(None, None)
