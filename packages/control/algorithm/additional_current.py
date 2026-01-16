import logging

from control.algorithm import common
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT
from control.limiting_value import LoadmanagementLimit
from control.load_protocol import Load
from control.loadmanagement import Loadmanagement
from control.algorithm.filter_chargepoints import (get_loads_by_mode_and_counter,
                                                   get_preferenced_load_charging)

log = logging.getLogger(__name__)


class AdditionalCurrent:

    def __init__(self) -> None:
        pass

    def set_additional_current(self) -> None:
        common.reset_current_by_chargemode(CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT)
        for counter in common.counter_generator():
            preferenced_loads, preferenced_loads_without_set_current = get_preferenced_load_charging(
                get_loads_by_mode_and_counter(CONSIDERED_CHARGE_MODES_ADDITIONAL_CURRENT,
                                              f"counter{counter.num}"))
            if preferenced_loads:
                common.update_raw_data(preferenced_loads)
                log.info(f"Zähler {counter.num}, Verbraucher {preferenced_loads}")
                while len(preferenced_loads):
                    load = preferenced_loads[0]
                    missing_currents, counts = common.get_missing_currents_left(preferenced_loads)
                    available_currents, limit = Loadmanagement().get_available_currents(missing_currents, counter, load)
                    log.debug(f"load {load.num} available currents {available_currents} missing currents "
                              f"{missing_currents} limit {limit.message}")
                    load.data.control_parameter.limit = limit
                    available_for_cp = common.available_current_for_load(
                        load, counts, available_currents, missing_currents)
                    current = common.get_current_to_set(
                        load.data.set.current, available_for_cp, load.data.set.target_current)
                    self._set_loadmangement_message(current, limit, load)
                    common.set_current_counterdiff(
                        load.data.control_parameter.min_current,
                        current,
                        load)
                    preferenced_loads.pop(0)
            if preferenced_loads_without_set_current:
                for load in preferenced_loads_without_set_current:
                    load.data.set.current = load.data.set.target_current

    # tested
    def _set_loadmangement_message(self,
                                   current: float,
                                   limit: LoadmanagementLimit,
                                   load: Load) -> None:
        # Strom muss an diesem Zähler geändert werden
        log.debug(
            f"current {current} target {load.data.set.target_current} set current {load.data.set.current}"
            f" required currents {load.data.control_parameter.required_currents}")
        if (current != max(load.data.set.target_current, load.data.set.current or 0) and
                # Strom erreicht nicht die vorgegebene Stromstärke
                round(current, 2) != round(max(
                    load.data.control_parameter.required_currents), 2)):
            load.set_state_and_log(f"Es kann nicht mit der vorgegebenen Stromstärke geladen werden"
                                   f"{limit.message}")
