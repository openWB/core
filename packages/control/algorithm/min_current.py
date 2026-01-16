import logging

from control import data
from control.algorithm import common
from control.algorithm.chargemodes import CONSIDERED_CHARGE_MODES_MIN_CURRENT, CONSIDERED_CHARGE_MODES_PV_ONLY
from control.chargepoint.chargepoint_state import ChargepointState
from control.loadmanagement import Loadmanagement
from control.algorithm.filter_chargepoints import get_loads_by_mode_and_counter

log = logging.getLogger(__name__)


class MinCurrent:

    def __init__(self) -> None:
        pass

    def set_min_current(self) -> None:
        for counter in common.counter_generator():
            preferenced_loads = get_loads_by_mode_and_counter(CONSIDERED_CHARGE_MODES_MIN_CURRENT,
                                                              f"counter{counter.num}",
                                                              full_power_considered=False)
            if preferenced_loads:
                log.info(f"Zähler {counter.num}, Verbraucher {preferenced_loads}")
                common.update_raw_data(preferenced_loads, diff_to_zero=True)
                while len(preferenced_loads):
                    load = preferenced_loads[0]
                    missing_currents, counts = common.get_min_current(load)
                    if max(missing_currents) > 0:
                        available_currents, limit = Loadmanagement().get_available_currents(
                            missing_currents, counter, load)
                        load.data.control_parameter.limit = limit
                        available_for_load = common.available_current_for_load(
                            load, counts, available_currents, missing_currents)
                        current = common.get_current_to_set(
                            load.data.set.current, available_for_load, load.data.set.target_current)
                        if current < load.data.control_parameter.min_current:
                            common.set_current_counterdiff(-(load.data.set.current or 0), 0, load)
                            if limit:
                                load.set_state_and_log(
                                    f"Ladung kann nicht gestartet werden{limit.message}")
                        else:
                            common.set_current_counterdiff(
                                load.data.set.target_current,
                                load.data.control_parameter.min_current,
                                load)
                    else:
                        if (load.data.control_parameter.chargemode,
                                load.data.control_parameter.submode) in CONSIDERED_CHARGE_MODES_PV_ONLY:
                            try:
                                if (load.data.control_parameter.state == ChargepointState.NO_CHARGING_ALLOWED or
                                        load.data.control_parameter.state == ChargepointState.SWITCH_ON_DELAY):
                                    data.data.counter_all_data.get_evu_counter().switch_on_threshold_reached(load)
                            except Exception:
                                log.exception(f"Fehler in der PV-gesteuerten Ladung bei {load.num}")
                        load.data.set.current = 0
                    preferenced_loads.pop(0)
