"""Begrenzt die Rate der Lade-/Stopp-Wechsel an der EVSE.

Manche Fahrzeuge gehen in einen Fehlerzustand, aus dem sie sich nicht mehr
selbst befreien, wenn die Ladefreigabe zu schnell hintereinander entzogen und
wieder erteilt wird. Dieser Filter erzwingt daher eine Mindest-Ein- und eine
Mindest-Aus-Zeit auf Register 1000.

**Der Filter hat Vorrang vor allem anderen.** Es gibt keine Umgehung. Ein
Schreibzugriff, der die Mindestzeiten verletzen würde, findet nicht statt --
auch nicht für Phasenumschaltung, CP-Unterbrechung oder Fehlerabschaltung. Wer
zwingend schreiben muss, wartet über :func:`wait_for_window`, bis er darf.

Drei Eigenschaften, die gelten müssen:

1. **Nur der Wechsel 0 <-> ungleich 0 wird begrenzt.** Eine Änderung von 6A auf
   10A läuft immer durch, sonst wäre die Überschussregelung ausgehebelt.
2. **Der Filter verzögert, er verwirft nicht.** Bei ``False`` kehrt
   ``set_current`` vor ``write_register`` zurück, ``evse_current`` behält also
   weiterhin den zuletzt vom Gerät *gelesenen* Wert. Die Regelung stellt ihren
   Wunsch im nächsten Zyklus erneut, ein dauerhafter Befehl landet also, sobald
   das Fenster abgelaufen ist. Ein Ein-Zyklus-Zappler wird vollständig
   geschluckt: der 0-Schreibzugriff wird unterdrückt, der darauf folgende
   ungleich-0-Schreibzugriff ist wegen des unveränderten ``evse_current`` ein
   No-Op.
3. **Wer nicht einfach den nächsten Zyklus abwarten kann, wartet aktiv.**
   Phasenumschaltung und CP-Unterbrechung schalten Hardware in dem Moment, in
   dem sie den Strom auf 0 setzen. Würde dieser Schreibzugriff nur unterdrückt
   und die Prozedur liefe weiter, schaltete das Relais unter Last. Diese
   Prozeduren laufen ohnehin in eigenen Threads (siehe
   ``control/phase_switch.py``) und blockieren daher über
   :func:`wait_for_window`, bis die Abschaltung erlaubt ist. Kommt die Freigabe
   nicht rechtzeitig, unterbleibt die Umschaltung -- sie wird später erneut
   angefordert.
4. **Die abgewartete Abschaltung zieht kein neues Fenster auf.** Sie wird zwar
   protokolliert und für die Relay-Loop-Diagnose gezählt, setzt aber
   ``last_zero_ts`` nicht (``arm_window=False`` in :func:`record_write`).
   Andernfalls wäre der Wiederanlauf direkt nach der Umschaltung für
   ``MIN_OFF_TIME_S`` gesperrt, das Fahrzeug bekäme also minutenlang 0A
   angeboten -- obwohl der Aufrufer die Mindest-Ein-Zeit bereits voll
   abgewartet hat. Das ist keine Umgehung: geschaltet wird erst, wenn das
   Fenster offen ist; nur die Buchführung danach unterbleibt.

Der Zustand liegt bewusst auf Modul-Ebene und wird über ``evse_id`` getrennt
gehalten.
"""
import logging
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from threading import Lock
from typing import Dict, List, Optional
import time

from helpermodules.logger import FORMAT_STR_SHORT, PERSISTENT_LOG_PATH

# Aus dem alten Fork übernommen und im Feld bestätigt. Die Fenster sind
# absichtlich deutlich länger als switch_off_delay der Regelung; siehe
# Abschnitt 4.4 des Portierungsplans. Nicht "passend" kürzen.
MIN_ON_TIME_S = 300.0    # wie lange ein ungleich-0-Wert stehen muss, bevor 0 geschrieben werden darf
MIN_OFF_TIME_S = 300.0   # wie lange eine 0 stehen muss, bevor wieder ungleich 0 geschrieben werden darf

# Obergrenze für wait_for_window. Ein berechtigtes Warten dauert nie länger als
# das größere der beiden Fenster; der Rest ist Sicherheitsmarge für den Fall,
# dass ein anderer Thread das Fenster zwischendurch neu aufzieht.
MAX_WAIT_S = max(MIN_ON_TIME_S, MIN_OFF_TIME_S) + 30.0
WAIT_POLL_S = 1.0

# Reine Diagnose, ohne Einfluss auf das Verhalten.
TOGGLE_WINDOW_S = 120.0
TOGGLE_WARN_COUNT = 3

LOG_FILE = "openwb_evse_relay.log"

log = logging.getLogger("evse_relay")


def _setup_logger() -> None:
    log.propagate = False
    try:
        handler = RotatingFileHandler(PERSISTENT_LOG_PATH + LOG_FILE, maxBytes=1000000, backupCount=1)
    except OSError:
        # Kein Log-Verzeichnis (z.B. Entwicklungsrechner): an den Root-Logger
        # durchreichen, statt den Import scheitern zu lassen.
        log.propagate = True
        return
    handler.setFormatter(logging.Formatter(FORMAT_STR_SHORT))
    log.addHandler(handler)


if not log.handlers:
    _setup_logger()


@dataclass
class _EvseState:
    last_zero_ts: float = 0.0
    last_nonzero_ts: float = 0.0
    # None: es wurde noch nichts geschrieben, es gibt also nichts zu begrenzen.
    last_was_zero: Optional[bool] = None
    transitions: List[float] = field(default_factory=list)


_states: Dict[int, _EvseState] = {}
# Der interne Ladepunkt, die Phasenumschaltung und die CP-Unterbrechung laufen
# jeweils in eigenen Threads, daher ein Lock.
_lock = Lock()


def _state(evse_id: int) -> _EvseState:
    state = _states.get(evse_id)
    if state is None:
        state = _EvseState()
        _states[evse_id] = state
    return state


def remaining(evse_id: int, formatted_current: int) -> float:
    """Wie lange ist dieser Schreibzugriff noch gesperrt?

    :return: Restzeit in Sekunden, 0.0 wenn sofort geschrieben werden darf.
             Protokolliert bewusst nichts, damit Warteschleifen das Log nicht
             fluten.
    """
    with _lock:
        state = _state(evse_id)
        is_zero = formatted_current == 0
        if state.last_was_zero is None or is_zero == state.last_was_zero:
            # Erster Schreibzugriff, oder reine Änderung der Stromstärke.
            return 0.0
        now = time.monotonic()
        if is_zero:
            return max(0.0, MIN_ON_TIME_S - (now - state.last_nonzero_ts))
        return max(0.0, MIN_OFF_TIME_S - (now - state.last_zero_ts))


def allow_write(evse_id: int, formatted_current: int) -> bool:
    """Darf dieser Schreibzugriff auf Register 1000 jetzt raus?

    :return: True -> schreiben. False -> diesen Zyklus überspringen, die
             Regelung stellt den Wunsch im nächsten Zyklus erneut.
    """
    try:
        left = remaining(evse_id, formatted_current)
        if left > 0:
            kind = "zero" if formatted_current == 0 else "non-zero"
            log.warning(f"EVSE id={evse_id}: {kind}-write suppressed, {left:.1f}s left in window")
            return False
        return True
    except Exception:
        # Im Zweifel schreiben lassen: Upstream-Verhalten ist das sichere Fallback.
        log.exception("Fehler im EVSE-Übergangsfilter")
        return True


def wait_for_window(evse_id: int, formatted_current: int, timeout: float = MAX_WAIT_S) -> bool:
    """Blockiert, bis der Schreibzugriff erlaubt ist.

    Nur für Aufrufer, die den Schreibzugriff nicht einfach im nächsten Zyklus
    wiederholen können, weil sie unmittelbar danach Hardware schalten.

    :return: True -> es darf geschrieben werden. False -> das Fenster ging
             innerhalb von ``timeout`` nicht auf; der Aufrufer muss seine
             Prozedur abbrechen und darf **nicht** trotzdem schalten.
    """
    try:
        left = remaining(evse_id, formatted_current)
        if left <= 0:
            return True
        log.warning(f"EVSE id={evse_id}: warte {left:.1f}s auf das Freigabefenster, bevor geschaltet wird")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(min(WAIT_POLL_S, left))
            left = remaining(evse_id, formatted_current)
            if left <= 0:
                log.warning(f"EVSE id={evse_id}: Freigabefenster offen, Schaltvorgang wird fortgesetzt")
                return True
        log.error(f"EVSE id={evse_id}: Freigabefenster ging nicht innerhalb von {timeout:.0f}s auf, "
                  "Schaltvorgang wird abgebrochen")
        return False
    except Exception:
        log.exception("Fehler im EVSE-Übergangsfilter")
        # Fail-safe statt fail-open: hier hängt ein Schaltvorgang dran, der
        # unter Last nicht stattfinden darf.
        return False


def record_write(evse_id: int, formatted_current: int, arm_window: bool = True) -> None:
    """Meldet einen tatsächlich erfolgten Schreibzugriff zurück.

    :param arm_window: False für Schreibzugriffe, die über :func:`wait_for_window`
                       bereits auf das Fenster gewartet haben. Sie werden
                       protokolliert und gezählt, ziehen aber kein neues Fenster
                       auf -- siehe Punkt 4 im Modul-Docstring.
    """
    try:
        with _lock:
            state = _state(evse_id)
            is_zero = formatted_current == 0
            now = time.monotonic()
            # Einzige positive Spur eines echten Schreibzugriffs auf Register 1000: ohne sie ist im Log
            # nicht unterscheidbar, ob nichts geschrieben wurde oder nur nichts unterdrückt wurde.
            log.warning(f"EVSE id={evse_id}: register 1000 written, value={formatted_current}"
                        f"{'' if arm_window else ' (awaited, window not re-armed)'}")
            if arm_window:
                if is_zero:
                    state.last_zero_ts = now
                else:
                    state.last_nonzero_ts = now
            if state.last_was_zero is not None and is_zero != state.last_was_zero:
                state.transitions.append(now)
                state.transitions = [t for t in state.transitions if now - t <= TOGGLE_WINDOW_S]
                if len(state.transitions) >= TOGGLE_WARN_COUNT:
                    log.warning(f"EVSE id={evse_id}: {len(state.transitions)} zero/non-zero toggles "
                                f"in {TOGGLE_WINDOW_S:.0f}s — possible relay loop!")
            state.last_was_zero = is_zero
    except Exception:
        log.exception("Fehler im EVSE-Übergangsfilter")


def reset() -> None:
    """Verwirft den kompletten Zustand. Nur für Tests."""
    with _lock:
        _states.clear()
