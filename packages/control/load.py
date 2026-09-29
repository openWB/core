
import logging

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.load_protocol import Load


log = logging.getLogger(__name__)

# Zustände, in denen reserved_surplus/released_surplus gerade eine laufende Reservierung halten (siehe die
# jeweiligen += beim Eintritt und -= beim Verlassen dieser Zustände in counter.py/ev.py/chargepoint.py).
# NO_CHARGING_ALLOWED gehört bewusst nicht dazu: jede Reservierung wird spätestens beim Übergang in diesen
# Zustand bereits wieder freigegeben (siehe zB Counter.reset_switch_on_off()), er wird hier also nie mit einer
# noch offenen Reservierung erreicht.
RESERVATION_HOLDING_STATES = (ChargepointState.PERFORMING_PHASE_SWITCH,
                              ChargepointState.PHASE_SWITCH_DELAY,
                              ChargepointState.SWITCH_OFF_DELAY,
                              ChargepointState.SWITCH_ON_DELAY)


def reset_pv_data_if_no_active_delays() -> None:
    """ Wenn keine Komponente gerade eine Reservierung offen hält, werden die Algorithmus-Werte
    zurückgesetzt.
    (dient der Robustheit)
    """
    try:
        for load in list(data.data.cp_data.values()) + list(data.data.consumer_data.values()):
            try:
                if load.data.control_parameter.state in RESERVATION_HOLDING_STATES:
                    break
            except Exception:
                log.exception(f"Fehler beim Bereinigen der Werte für Ladepunkt/Verbraucher {load.num}")
        else:
            data.data.counter_all_data.get_evu_counter().reset_pv_data()
    except Exception:
        log.exception("Fehler beim Bereinigen der Werte")


def get_load_str(load: Load) -> str:
    if isinstance(load, Chargepoint):
        return f"Ladepunkt {load.num}"
    else:
        return f"Verbraucher {load.num}"
