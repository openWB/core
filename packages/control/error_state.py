""" Gate für Komponenten, die nach andauerndem Fehler nicht mehr aktiv angesteuert werden sollen (zB aktive
Speichersteuerung, Verbraucher-Schaltbefehle). Das Nullen der Leistung selbst passiert im Modul
(modules/common/fault_state.py::FaultState.on_sustained_error). """
from typing import Optional

from helpermodules import timecheck
from helpermodules.constants import COMPONENT_ERROR_DURATION
from modules.common.fault_state_level import FaultStateLevel


def tick_error_timer(fault_state: int, error_timer: Optional[float]) -> Optional[float]:
    if fault_state == FaultStateLevel.ERROR:
        return error_timer if error_timer is not None else timecheck.create_timestamp()
    return None


def error_duration_exceeded(fault_state: int, error_timer: Optional[float]) -> bool:
    """ analog zu ErrorTimerContext.error_counter_exceeded() (helpermodules/utils/error_handling.py) """
    return (fault_state == FaultStateLevel.ERROR and error_timer is not None and
            timecheck.check_timestamp(error_timer, COMPONENT_ERROR_DURATION) is False)
