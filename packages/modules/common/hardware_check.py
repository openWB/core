from typing import Optional

from modules.common.component_state import CounterState
from modules.common.fault_state import FaultState


READ_METER_VOLTAGES_AGAIN = "Erneutes Auslesen der Spannungen am Zähler: {}V"


def check_meter_values(counter_state: CounterState, fault_state: Optional[FaultState] = None) -> None:
    meter_msg = check_meter(counter_state)
    if fault_state and meter_msg:
        fault_state.warning(meter_msg)


def check_meter(counter_state: CounterState) -> Optional[str]:
    # Nur prüfen, dass keine Phase ausgefallen ist
    # Es gibt einige Fälle, in denen die Normtoleranzen der Netzspannung nicht eingehalten werden, aber kein Defekt
    # vorliegt und der Kunde nicht eingreifen muss. Dann soll keine Warnung angezeigt werden.
    # Kona 1-phasig induziert auf L2 40V, Zoe auf L2 130V
    # beim Ladestart sind Strom und Spannung nicht immer konsistent.
    voltages = counter_state.voltages
    if (voltages[1] == 0 and voltages[2] > 30) or voltages[0] == 0:
        return READ_METER_VOLTAGES_AGAIN.format(voltages)
    return None
