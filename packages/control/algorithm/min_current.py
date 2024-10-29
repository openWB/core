from enum import Enum
import logging
from typing import List, Optional

from control import data
from control.algorithm import common
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_MIN_CURRENT
from control.chargepoint.chargepoint import Chargepoint
from control.counter import Counter
from control.loadmanagement import Loadmanagement
from control.algorithm.filter_chargepoints import get_chargepoints_by_mode_and_counter

log = logging.getLogger(__name__)


class LoadmanagementState(Enum):
    COUNTERS = 1
    CONTROLLABLE_CONSUMERS = 2


class MinCurrent:

    def __init__(self) -> None:
        pass

    def set_min_current(self) -> None:
        def set(loadmanagement_state: LoadmanagementState,
                preferenced_chargepoints: List[Chargepoint],
                counter: Optional[Counter] = None):
            common.update_raw_data(preferenced_chargepoints, diff_to_zero=True)
            for cp in preferenced_chargepoints:
                log.info(f"Mode-Tuple {mode_tuple[0]} - {mode_tuple[1]} - {mode_tuple[2]}" +
                         f", Zähler {counter.num}" if loadmanagement_state == LoadmanagementState.COUNTERS else "")
                missing_currents, counts = common.get_min_current(cp)
                if max(missing_currents) > 0:
                    if loadmanagement_state == LoadmanagementState.COUNTERS:
                        available_currents, limit = Loadmanagement().get_available_currents(
                            missing_currents, counter, cp)
                    else:
                        available_currents, limit = Loadmanagement().get_currents_controllable_consumers(
                            missing_currents, cp)
                    cp.data.control_parameter.limit = limit
                    available_for_cp = common.available_current_for_cp(
                        cp, counts, available_currents, missing_currents)
                    current = common.get_current_to_set(
                        cp.data.set.current, available_for_cp, cp.data.set.target_current)
                    if current < cp.data.control_parameter.min_current:
                        common.set_current_counterdiff(-(cp.data.set.current or 0), 0, cp)
                        if limit:
                            cp.set_state_and_log(f"Ladung kann nicht gestartet werden{limit}")
                    else:
                        common.set_current_counterdiff(
                            cp.data.set.target_current,
                            cp.data.control_parameter.min_current,
                            cp)
                else:
                    cp.data.set.current = 0

        for mode_tuple in CONSIDERED_CHARGE_MODES_MIN_CURRENT:
            # erstmal SteuVE prüfen, da nicht alle LP dazu zählen müssen und wenn einige dadurch begrenzt werden,
            # # können andere die Zählergrenzen noch voll ausnutzen
            preferenced_chargepoints_mode = common.get_chargepoints_by_mode(mode_tuple)
            set(LoadmanagementState.CONTROLLABLE_CONSUMERS, preferenced_chargepoints_mode)

            for counter in common.counter_generator():
                preferenced_chargepoints = get_chargepoints_by_mode_and_counter(mode_tuple, f"counter{counter.num}")
                set(LoadmanagementState.COUNTERS, preferenced_chargepoints, counter=counter)

            # Verbleibende Dimm-Leistung erst am Ende setzen, da die Zähler auch noch begrenzen können. Aktuell wird aber für mehrere LPs auf einer Ebene erst am Ende gestetzt.
            for cp in preferenced_chargepoints_mode:
                data.data.io_actions.dimming_set_import_power_left(
                    cp.num, cp.data.control_parameter.phases*cp.data.set.current)
