"""prüft, ob Zeitfenster aktuell sind
"""
import logging
import datetime
from typing import Dict, List, Optional, Tuple, Union

from control.ev import ScheduledChargingPlan, TimeChargingPlan

log = logging.getLogger(__name__)


def set_date(now: datetime.datetime,
             begin: datetime.datetime,
             end: datetime.datetime) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """ setzt das Datum auf das heutige Datum, bzw. falls der Endzeitpunkt am nächsten Tag ist, auf morgen
    """
    try:
        begin = begin.replace(now.year, now.month, now.day)
        end = end.replace(now.year, now.month, now.day)
        if begin > end:
            # Endzeit ist am nächsten Tag
            end = end + datetime.timedelta(days=1)
        return begin, end
    except Exception:
        log.exception("Fehler im System-Modul")
        return None, None


def is_timeframe_valid(now: datetime.datetime, begin: datetime.datetime, end: datetime.datetime) -> bool:
    """ überprüft, ob das Zeitfenster des Ladeplans aktuell ist.
    Returns
    -------
    True : aktuell
    False : nicht aktuell
    """
    try:
        if (not (now < begin)) and ((now < end)):
            return True
        else:
            return False
    except Exception:
        log.exception("Fehler im System-Modul")
        return False


def is_autolock_plan_active(plans: Dict) -> bool:
    for plan in plans:
        if is_autolock_of_plan_active(plans[plan]):
            return True
    else:
        return False


def is_autolock_of_plan_active(plan: Dict) -> bool:
    if plan["active"]:
        now = datetime.datetime.today()
        lock: datetime.datetime
        unlock: datetime.datetime
        if plan["frequency"]["selected"] == "once":
            lock = datetime.datetime.strptime(
                plan.frequency.once[0] + plan["time"][0], "%Y-%m-%d%H:%M")
            unlock = datetime.datetime.strptime(
                plan.frequency.once[1] + plan["time"][1], "%Y-%m-%d%H:%M")
        else:
            lock, unlock = set_date(
                now, datetime.datetime.strptime(plan["time"][0], '%H:%M'),
                datetime.datetime.strptime(plan["time"][1], '%H:%M'))
            if plan["frequency"]["selected"] == "weekly" and not plan[
                    "frequency"]["weekly"][now.weekday()]:
                # Tag ist nicht konfiguriert
                return False
        return is_now_in_locking_time(now, lock, unlock)
    return False


def is_now_in_locking_time(now: datetime.datetime,
                           lock: datetime.datetime,
                           unlock: datetime.datetime) -> bool:
    # Es gibt nur einen Entsperrzeitpunkt.
    if lock is None:
        if now < unlock:
            return True
        else:
            return False
    elif unlock is None:
        if now < lock:
            return False
        else:
            return True
    # Sperrzeitpunkt liegt vor Entsperrzeitpunkt
    elif lock < unlock:
        # Laden - Sperrzeitpunkt - nicht laden -Entsperrzeitpunkt - laden
        if now < lock or unlock < now:
            return False
        else:
            return True
    # Entsperrzeitpunkt liegt vor Sperrzeitpunkt
    else:
        # nicht Laden - Entsperrzeitpunkt - laden - Sperrzeitpunkt - nicht laden
        if now < lock or unlock < now:
            return True
        else:
            return False


def check_plans_timeframe(plans: Dict[int, TimeChargingPlan]) -> Optional[TimeChargingPlan]:
    """ geht alle Pläne durch.

    Parameters
    ----------
    plans: Dictionary
        Liste der Pläne, deren Zeitfenster geprüft werden sollen

    Returns
    -------
    plan: erster aktiver Plan
    None: falls kein Plan aktiv ist
    """
    state = False
    try:
        for plan in plans.values():
            # Nur Keys mit Plan-Nummer berücksichtigen
            if isinstance(plan, TimeChargingPlan):
                state = check_timeframe(plan)
                if state:
                    return plan
        else:
            return None
    except Exception:
        log.exception("Fehler im System-Modul")
        return None


def check_timeframe(plan: Union[ScheduledChargingPlan, TimeChargingPlan], hours: Optional[int] = None):
    """ schaut, ob Pläne aktiv sind, prüft, ob das Zeitfenster aktuell ist.

    Parameters
    ----------
    plan: Dictionary
        Plan dessen Zeitfenster geprüft werden soll
    hours = None: int
        Stunden, die der Beginn vorher liegen soll; Werden keine Stunden angegeben, wird der Beginn dem Dictionary
        entnommen.

    Returns
    -------
    True: Zeitfenster gültig
    False: Zeitfenster nicht gültig
    """
    state = None
    try:
        if plan.active:
            now = datetime.datetime.today()
            if hours is None:
                begin = datetime.datetime.strptime(plan.time[0], '%H:%M')
                end = datetime.datetime.strptime(plan.time[1], '%H:%M')
            else:
                end = datetime.datetime.strptime(plan.time, '%H:%M')

            if plan.frequency.selected == "once":
                if hours is None:
                    beginDate = datetime.datetime.strptime(plan.frequency.once[0], "%Y-%m-%d")
                    begin = begin.replace(beginDate.year, beginDate.month,
                                          beginDate.day)
                    endDate = datetime.datetime.strptime(plan.frequency.once[1], "%Y-%m-%d")
                else:
                    endDate = datetime.datetime.strptime(plan.frequency.once, "%Y-%m-%d")
                    end = end.replace(endDate.year, endDate.month, endDate.day)
                    begin = _calc_begin(end, hours)
                end = end.replace(endDate.year, endDate.month, endDate.day)
                state = is_timeframe_valid(now, begin, end)

            elif plan.frequency.selected == "daily":
                if hours is None:
                    begin, end = set_date(now, begin, end)
                else:
                    end = end.replace(now.year, now.month, now.day)
                    # Wenn der Zeitpunkt an diesem Tag schon vorüber ist, nächsten Tag prüfen.
                    if end < now:
                        end += datetime.timedelta(days=1)
                    begin = _calc_begin(end, hours)
                state = is_timeframe_valid(now, begin, end)

            elif plan.frequency.selected == "weekly":
                if hours is None:
                    if begin < end:
                        # Endzeit ist am gleichen Tag
                        if plan.frequency.weekly[now.weekday()]:
                            begin, end = set_date(now, begin, end)
                            state = is_timeframe_valid(now, begin, end)
                        else:
                            state = False
                    else:
                        if (plan.frequency.weekly[now.weekday()]
                                or plan.frequency.weekly[now.weekday() +
                                                         1]):
                            begin, end = set_date(now, begin, end)
                            state = is_timeframe_valid(now, begin, end)
                        else:
                            state = False
                else:
                    if plan.frequency.weekly[now.weekday()]:
                        end = end.replace(now.year, now.month, now.day)
                        begin = _calc_begin(end, hours)
                        state = is_timeframe_valid(now, begin, end)
                    else:
                        state = False
    except Exception:
        log.exception("Fehler im System-Modul")
        return None
    return state


def _calc_begin(end: datetime.datetime, hours: int) -> datetime.datetime:
    """ berechnet den Zeitpunkt, der die angegebenen Stunden vor dem Endzeitpunkt liegt.
    """
    prev = datetime.timedelta(hours)
    return end - prev


def check_duration(plan: ScheduledChargingPlan, duration: float) -> Tuple[int, float]:
    """ prüft, ob der in angegebene Zeitpunkt abzüglich der Dauer jetzt ist.
    Um etwas Puffer zu haben, werden bei Überschreiten des Zeitpunkts die nachfolgenden 20 Min auch noch als Ladezeit
    zurückgegeben.

    Return
    ------
    2, int: Zeitpunkt ist um mehr als 5 Min überschritten worden, verbleibende Zeit in h
    1, 0: Ladung sollte starten
    0, 0: hat noch Zeit
    """
    now = datetime.datetime.today()
    end = datetime.datetime.strptime(plan.time, '%H:%M')

    if plan.frequency.selected == "once":
        endDate = datetime.datetime.strptime(plan.frequency.once, "%Y-%m-%d")
        end = end.replace(endDate.year, endDate.month, endDate.day)
        state, remaining_time = _is_duration_valid(now, duration, end)
        if -0.33 <= remaining_time < 0:
            remaining_time = remaining_time * -1
        elif remaining_time < -0.33:
            state = 0
            remaining_time = 0
        return state, remaining_time

    elif plan.frequency.selected == "daily":
        end = end.replace(now.year, now.month, now.day)
        # Wenn der Zeitpunkt an diesem Tag schon vorüber ist (verbleibende Zeit ist negativ), nächsten Tag prüfen.
        state, remaining_time = _is_duration_valid(now, duration, end)
        # Bis zwanzig Minuten nach Überschreiten des Zeitpunkts darf noch geladen werden.
        if -0.33 <= remaining_time < 0:
            remaining_time = remaining_time * -1
        elif remaining_time < -0.33:
            delta = datetime.timedelta(days=1)
            end += delta
            state, remaining_time = _is_duration_valid(now, duration, end)
        return state, remaining_time
    elif plan.frequency.selected == "weekly":
        if plan.frequency.weekly[now.weekday()]:
            end = end.replace(now.year, now.month, now.day)
            state, remaining_time = _is_duration_valid(now, duration, end)
            # Zeitpunkt ist an diesem Tag noch nicht vorbei
            if state == 1:
                return state, remaining_time
            elif -0.33 <= remaining_time < 0:
                remaining_time = remaining_time * -1
            else:
                # Wenn der Zeitpunkt an diesem Tag schon vorüber ist (verbleibende Zeit ist negativ), nächsten Tag
                # prüfen.
                delta = datetime.timedelta(days=1)
                end += delta
                state, remaining_time = _is_duration_valid(
                    now, duration, end)
            return state, remaining_time
        # prüfen, ob für den nächsten Tag ein Termin ansteht und heute schon begonnen werden muss
        if plan.frequency.weekly[now.weekday() + 1]:
            end = end.replace(now.year, now.month, now.day)
            delta = datetime.timedelta(days=1)
            end += delta
            return _is_duration_valid(now, duration, end)
        else:
            return 0, 0
    else:
        raise TypeError(f'Unbekannte Häufigkeit {plan.frequency.selected}')


def _is_duration_valid(now: datetime.datetime, duration: float, end: datetime.datetime):
    """ prüft, ob der Endzeitpunkt der Ladung abzüglich der Ladedauer in den nächsten 5 Min liegt oder schon vorüber
    ist.

    Return
    ------
    2, int: Zeitpunkt ist um mehr als 5 Min überschritten worden, verbleibende Zeit in h
    1, 0: Ladung sollte starten
    0, 0: hat noch Zeit
    """
    try:
        delta = datetime.timedelta(hours=int(duration), minutes=((duration % 1) * 60))
        begin = end - delta
        difference = (now - begin).total_seconds()
        if difference > 0:
            remaining_time = duration - (difference / 3600)
            return 2, remaining_time
        elif difference > (-300):
            return 1, 0
        else:
            return 0, 0
    except Exception:
        log.exception("Fehler im System-Modul")
        return 1, 0


def is_list_valid(hourlist: List[int]) -> bool:
    """ prüft, ob eine der angegebenen Unix-Zeiten aktuell ist.

    Parameter
    ---------
    hourlist: list
        Liste mit Unix-Zeiten

    Return
    ------
    True: aktuelle Stunde ist in der Liste enthalten
    False: aktuelle Stunde ist nicht in der Liste enthalten
    """
    try:
        now = datetime.datetime.today()
        for hour in hourlist:
            timestamp = datetime.datetime.fromtimestamp(float(hour))
            if timestamp.hour == now.hour:
                return True
            else:
                return False
        else:
            return False
    except Exception:
        log.exception("Fehler im System-Modul")
        return False


def check_timestamp(timestamp: str, duration: int) -> bool:
    """ prüft, ob der Zeitstempel innerhalb der angegebenen Zeit liegt

    Parameter
    ---------
    timestamp: str
        Zeitstempel, der geprüft werden soll
    duration:
        Zeitspanne in s, in der der Zeitstempel gültig ist

    Return
    ------
    True: Zeit ist noch nicht abgelaufen
    False: Zeit ist abgelaufen
    """
    try:
        stamp = datetime.datetime.strptime(timestamp, "%m/%d/%Y, %H:%M:%S")
        now = datetime.datetime.today()
        delta = datetime.timedelta(seconds=duration)
        if (now - delta) > stamp:
            return False
        else:
            return True
    except Exception:
        log.exception("Fehler im System-Modul")
        return True


def create_timestamp() -> str:
    try:
        stamp = datetime.datetime.today().strftime("%m/%d/%Y, %H:%M:%S")
        return stamp
    except Exception:
        raise


def create_timestamp_unix() -> int:
    """ Unix Zeitstempel
    """
    try:
        return int(datetime.datetime.now().timestamp())
    except Exception:
        raise


def create_timestamp_YYYYMM() -> str:
    try:
        stamp = datetime.datetime.today().strftime("%Y%m")
        return stamp
    except Exception:
        raise


def create_timestamp_YYYYMMDD() -> str:
    try:
        stamp = datetime.datetime.today().strftime("%Y%m%d")
        return stamp
    except Exception:
        raise


def create_timestamp_time() -> str:
    try:
        stamp = datetime.datetime.today().strftime("%H:%M")
        return stamp
    except Exception:
        raise


def get_difference_to_now(timestamp_begin: str) -> str:
    """ ermittelt den Abstand zwischen zwei Zeitstempeln.

    Parameter
    ---------
    timestamp_begin: str %m/%d/%Y, %H:%M:%S
        Anfangszeitpunkt

    Return
    ------
    diff: str
        Differenz HH:MM, ggf DD days, HH:MM
    """
    try:
        begin = datetime.datetime.strptime(timestamp_begin[:-3], "%m/%d/%Y, %H:%M")
        now = datetime.datetime.today()
        diff = (now - begin)
        return __convert_timedelta_to_HHMM(diff)
    except Exception:
        log.exception("Fehler im System-Modul")
        return "00:00"


def get_difference(timestamp_begin: str, timestamp_end: str) -> Optional[str]:
    """ ermittelt den Abstand zwischen zwei Zeitstempeln in absoluten Sekunden.

    Parameter
    ---------
    timestamp_begin: str %m/%d/%Y, %H:%M:%S
        Anfangszeitpunkt
    timestamp_end: str %m/%d/%Y, %H:%M:%S
        Anfangszeitpunkt

    Return
    ------
    diff: int
        Differenz in Sekunden
    """
    try:
        begin = datetime.datetime.strptime(timestamp_begin, "%m/%d/%Y, %H:%M:%S")
        end = datetime.datetime.strptime(timestamp_end, "%m/%d/%Y, %H:%M:%S")
        diff = (begin - end)
        return f"{int(diff.total_seconds())}"
    except Exception:
        log.exception("Fehler im System-Modul")
        return None


def duration_sum(first: str, second: str) -> str:
    """ addiert zwei Zeitstrings und gibt das Ergebnis als String zurück.

    Parameter
    ---------
    first, second: str
        Zeitstrings HH:MM ggf DD:HH:MM
    Return
    ------
    sum: str
        Summe der Zeitstrings
    """
    try:
        sum = __get_timedelta_obj(first) + __get_timedelta_obj(second)
        return __convert_timedelta_to_HHMM(sum)
    except Exception:
        log.exception("Fehler im System-Modul")
        return "00:00"


def __get_timedelta_obj(time: str) -> datetime.timedelta:
    """ erstellt aus einem String ein timedelta-Objekt.

    Parameter
    ---------
    time: str
        Zeitstrings HH:MM ggf DD:HH:MM
    """
    time_charged = time.split(":")
    if len(time_charged) == 2:
        delta = datetime.timedelta(hours=int(time_charged[0]),
                                   minutes=int(time_charged[1]))
    elif len(time_charged) == 3:
        delta = datetime.timedelta(days=int(time_charged[0]),
                                   hours=int(time_charged[1]),
                                   minutes=int(time_charged[2]))
    else:
        raise Exception("Unknown charge duration: "+time)
    return delta


def __convert_timedelta_to_HHMM(timedelta_obj: datetime.timedelta) -> str:
    diff_hours = int(timedelta_obj.total_seconds() / 3600)
    diff_minutes = int((timedelta_obj.total_seconds() % 3600) / 60)
    return f"{diff_hours}:{diff_minutes:02d}"
