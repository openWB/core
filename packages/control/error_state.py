""" Hilfsfunktion, um bei andauerndem Fehlerzustand einer Komponente nach Ablauf einer Wartezeit nicht mehr mit
deren letztem bekannten Wert weiterzurechnen. Analog zu Counter._get_loadmanagement_state, aber für Komponenten,
die im Fehlerfall nicht auf einen konfigurierten Ersatzwert zurückfallen, sondern schlicht mit 0W nicht mehr
berücksichtigt werden sollen.
"""
from dataclasses import dataclass
from typing import Optional

from helpermodules import timecheck
from helpermodules.constants import COMPONENT_ERROR_DURATION
from modules.common.fault_state_level import FaultStateLevel


def error_duration_exceeded(fault_state: int, error_timer: Optional[float]) -> bool:
    """ analog zu ErrorTimerContext.error_counter_exceeded() (helpermodules/utils/error_handling.py) """
    return (fault_state == FaultStateLevel.ERROR and error_timer is not None and
            timecheck.check_timestamp(error_timer, COMPONENT_ERROR_DURATION) is False)


@dataclass
class EffectivePowerResult:
    power: float
    error_timer: Optional[float]
    just_expired: bool  # True genau in dem Zyklus, in dem die Wartezeit abgelaufen ist


def effective_power(power: float, fault_state: int, error_timer: Optional[float]) -> EffectivePowerResult:
    """ ermittelt, mit welcher Leistung für eine Komponente weitergerechnet werden soll.
    `power` selbst wird nicht verändert - nur der Rückgabewert.
    """
    if fault_state == FaultStateLevel.ERROR:
        if error_timer is None:
            return EffectivePowerResult(power, timecheck.create_timestamp(), False)
        elif error_duration_exceeded(fault_state, error_timer):
            return EffectivePowerResult(0, error_timer, power != 0)
        else:
            return EffectivePowerResult(power, error_timer, False)
    else:
        return EffectivePowerResult(power, None, False)
