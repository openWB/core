import logging
import operator
from typing import List, Optional, Tuple

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.limiting_value import LimitingValue
from modules.common.utils.component_parser import get_component_name_by_id


log = logging.getLogger(__name__)


class Loadmanagement:
    def get_available_currents(self,
                               missing_currents: List[float],
                               counter: Counter,
                               cp: Chargepoint,
                               feed_in: int = 0) -> Tuple[List[float], Optional[str]]:
        raw_currents_left = counter.data.set.raw_currents_left
        try:
            available_currents, limit = self._limit_by_dimming_via_direct_control(missing_currents, cp)

            available_currents, new_limit = self._limit_by_dimming(available_currents, cp)
            limit = new_limit if new_limit is not None else limit

            available_currents, new_limit = self._limit_by_ripple_control_receiver(available_currents, cp)
            limit = new_limit if new_limit is not None else limit
        except ValueError as e:
            available_currents = [0]*3
            limit = e.args[0]

        available_currents, new_limit = self._limit_by_current(counter, available_currents, raw_currents_left)
        limit = new_limit if new_limit is not None else limit

        available_currents, new_limit = self._limit_by_power(
            counter, available_currents, counter.data.set.raw_power_left, feed_in)
        limit = new_limit if new_limit is not None else limit

        if f"counter{counter.num}" == data.data.counter_all_data.get_evu_counter_str():
            available_currents, new_limit = self._limit_by_unbalanced_load(
                counter, available_currents, raw_currents_left,
                len([value for value in missing_currents if value != 0]))
            limit = new_limit if new_limit is not None else limit
        return available_currents, limit

    def get_available_currents_surplus(self,
                                       missing_currents: List[float],
                                       counter: Counter,
                                       cp: Chargepoint,
                                       feed_in: int = 0) -> Tuple[List[float], Optional[str]]:
        raw_currents_left = counter.data.set.raw_currents_left
        available_currents, limit = self._limit_by_dimming_via_direct_control(missing_currents, cp)

        available_currents, new_limit = self._limit_by_ripple_control_receiver(available_currents, cp)
        limit = new_limit if new_limit is not None else limit

        available_currents, new_limit = self._limit_by_current(counter, available_currents, raw_currents_left)
        limit = new_limit if new_limit is not None else limit

        available_currents, new_limit = self._limit_by_power(
            counter, available_currents, counter.data.set.surplus_power_left, feed_in)
        limit = new_limit if new_limit is not None else limit

        if f"counter{counter.num}" == data.data.counter_all_data.get_evu_counter_str():
            available_currents, new_limit = self._limit_by_unbalanced_load(
                counter, available_currents, raw_currents_left,
                len([value for value in missing_currents if value != 0]))
            limit = new_limit if new_limit is not None else limit
        return available_currents, limit

    def _limit_by_unbalanced_load(self,
                                  counter: Counter,
                                  available_currents: List[float],
                                  raw_currents_left: List[float],
                                  phases_to_use: int) -> Tuple[List[float], Optional[str]]:
        raw_currents_left_charging = list(map(operator.sub, raw_currents_left, available_currents))
        max_exceeding = counter.get_unbalanced_load_exceeding(raw_currents_left_charging)
        limit = None
        if max(max_exceeding) > 0:
            if phases_to_use < 3 and phases_to_use > 0:
                available_currents = list(map(operator.sub, available_currents, max_exceeding))
                log.debug(f"Schieflast {max_exceeding}A korrigieren: {available_currents}")
                limit = LimitingValue.UNBALANCED_LOAD.value.format(get_component_name_by_id(counter.num))
            elif phases_to_use == 3:
                log.debug("Schieflastkorrektur nicht möglich, da alle Phasen genutzt werden.")
        return available_currents, limit

    # tested
    def _limit_by_power(self,
                        counter: Counter,
                        available_currents: List[float],
                        raw_power_left: Optional[float],
                        feed_in: Optional[float]) -> Tuple[List[float], Optional[str]]:
        currents = available_currents.copy()
        limit = None
        if raw_power_left:
            if feed_in:
                raw_power_left = raw_power_left - feed_in
                log.debug(f"Verbleibende Leistung unter Berücksichtigung der Einspeisegrenze: {raw_power_left}W")
            if sum(available_currents)*230 > raw_power_left:
                for i in range(0, 3):
                    # Am meisten belastete Phase trägt am meisten zur Leistungsreduktion bei.
                    currents[i] = available_currents[i] / sum(available_currents) * raw_power_left / 230
                log.debug(f"Leistungsüberschreitung auf {raw_power_left}W korrigieren: {available_currents}")
                limit = LimitingValue.POWER.value.format(get_component_name_by_id(counter.num))
        return currents, limit

    # tested
    def _limit_by_current(self,
                          counter: Counter,
                          missing_currents: List[float],
                          raw_currents_left: List[float]) -> Tuple[List[float], Optional[str]]:
        available_currents = [0.0]*3
        limit = None
        for i in range(0, 3):
            available_currents[i] = min(missing_currents[i], raw_currents_left[i])
        if available_currents != missing_currents:
            log.debug(f"Stromüberschreitung {missing_currents}W korrigieren: {available_currents}")
            limit = LimitingValue.CURRENT.value.format(get_component_name_by_id(counter.num))
        return available_currents, limit

    def _limit_by_dimming_via_direct_control(self,
                                             missing_currents: List[float],
                                             cp: Chargepoint) -> Tuple[List[float], Optional[str]]:
        if data.data.io_actions.dimming_via_direct_control(cp.num):
            phases = 3-missing_currents.count(0)
            current_per_phase = 4.2/phases
            available_currents = [current_per_phase if c > 0 else 0 for c in missing_currents]
            log.debug(f"Dimmung per Direkt-Steuerung: {available_currents}A")
            return available_currents, LimitingValue.DIMMING_VIA_DIRECT_CONTROL.value
        else:
            return missing_currents, None

    def _limit_by_dimming(self,
                          available_currents: List[float],
                          cp: Chargepoint) -> Tuple[List[float], Optional[str]]:
        dimming_power_left = data.data.io_actions.dimming_get_import_power_left(cp.num)
        if dimming_power_left:
            if sum(available_currents)*230 > dimming_power_left:
                phases = 3-available_currents.count(0)
                overload_per_phase = (sum(available_currents) - dimming_power_left/230)/phases
                available_currents = [c - overload_per_phase if c > 0 else 0 for c in available_currents]
                log.debug(f"Reduzierung der Ströme durch die Dimmung: {available_currents}A")
                return available_currents, LimitingValue.DIMMING.value
        return available_currents, None

    def _limit_by_ripple_control_receiver(self,
                                          available_currents: List[float],
                                          cp: Chargepoint) -> Tuple[List[float], Optional[str]]:
        value = data.data.io_actions.ripple_control_receiver(cp.num)
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
            return available_currents, LimitingValue.RIPPLE_CONTROL_RECEIVER.value.format(value*100)
        else:
            return available_currents, None
