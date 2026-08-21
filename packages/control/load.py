
import logging

from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from control.load_protocol import Load


log = logging.getLogger(__name__)


def no_charge() -> None:
    """ Wenn keine EV angesteckt sind oder keine Verzögerungen aktiv sind, werden die Algorithmus-Werte
    zurückgesetzt.
    (dient der Robustheit)
    """
    try:
        for load in list(data.data.cp_data.values()) + list(data.data.consumer_data.values()):
            try:
                control_parameter = load.data.control_parameter
                # Kein EV, das Laden soll
                # Kein EV, das auf das Ablaufen der Einschalt- oder Phasenumschaltverzögerung wartet
                if (control_parameter.state != ChargepointState.PERFORMING_PHASE_SWITCH and
                    control_parameter.state != ChargepointState.PHASE_SWITCH_DELAY and
                    control_parameter.state != ChargepointState.SWITCH_OFF_DELAY and
                    control_parameter.state != ChargepointState.SWITCH_ON_DELAY and
                        control_parameter.state != ChargepointState.NO_CHARGING_ALLOWED):
                    continue
                else:
                    break
            except Exception:
                log.exception("Fehler beim Bereinigen der Werte für Ladepunkt/Verbraucher "+load.num)
        else:
            data.data.counter_all_data.get_evu_counter().reset_pv_data()
    except Exception:
        log.exception("Fehler beim Bereinigen der Werte")


def get_load_str(load: Load) -> str:
    if isinstance(load, Chargepoint):
        return f"Ladepunkt {load.num}"
    else:
        return f"Verbraucher {load.num}"
