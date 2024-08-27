""" Sim Count
Berechnet die importierte und exportierte Leistung, wenn der Zähler / PV-Modul / Speicher diese nicht liefert.
"""
import logging
import math
import time

from control import data as data_module
from modules.common.simcount._calculate import calculate_import_export
from modules.common.simcount.simcounter_state import SimCounterState
from modules.common.simcount._simcounter_store import get_sim_counter_store, restore_last_energy

log = logging.getLogger(__name__)


def sim_count(power_present: float, topic: str = "", data: SimCounterState = None, prefix: str = "") -> SimCounterState:
    """ emulate import export

    Parameters
    ----------
    power_present: aktuelle Leistung
    topic: Topic, für den Broker
    data: bisheriger state
    prefix: prefix für die ramdisk-Datei

    Return
    ------
    neuer state
    """
    store = get_sim_counter_store()
    timestamp_present = time.time()
    previous_state = store.load(prefix, topic) if data is None else data

    if math.isnan(power_present):
        raise ValueError("power_present is NaN.")

    if isinstance(power_present, (int, float)):
        if previous_state is None:
            log.debug("No previous state found. Starting new simulation.")
            return store.initialize(prefix, topic, power_present, timestamp_present)
        else:
            log.debug("Previous state: %s", previous_state)
            if math.isnan(previous_state.imported):
                log.error("imported is NaN. Reset simcount state.")
                previous_state.imported = restore_last_energy(topic, "imported")
            if math.isnan(previous_state.exported):
                log.error("exported is NaN. Reset simcount state.")
                previous_state.exported = restore_last_energy(topic, "exported")
            control_interval = data_module.data.general_data.data.control_interval
            if 2 * control_interval < timestamp_present - previous_state.timestamp:
                log.warning("Time difference between previous state and current state is too large. "
                            "Set time difference to control interval.")
                hours_since_previous = control_interval / 3600
            else:
                hours_since_previous = (timestamp_present - previous_state.timestamp) / 3600
            imported, exported = calculate_import_export(hours_since_previous, previous_state.power, power_present)
            if math.isnan(imported) or math.isnan(exported):
                raise ValueError("imported or exported is NaN. Retain previous state.")
            current_state = SimCounterState(
                timestamp_present,
                power_present,
                previous_state.imported + imported,
                previous_state.exported + exported
            )
            log.debug("imported: %g Wh, exported: %g Wh, new state: %s", imported, exported, current_state)
            store.save(prefix, topic, current_state)
            return current_state
