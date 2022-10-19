"""prüft, ob Zeitfenster aktuell sind
"""
import logging
import datetime
from typing import Dict, List, Optional, Tuple, TypeVar, Union

from helpermodules.abstract_plans import AutolockPlan, ScheduledChargingPlan, TimeChargingPlan

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


T = TypeVar("T", AutolockPlan, TimeChargingPlan)


def check_plans_timeframe(plans: Dict[int, T]) -> Optional[T]:
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


def check_duration(plan: ScheduledChargingPlan, duration: float, buffer: int) -> Tuple[Optional[float], bool]:
    """ prüft, ob der in angegebene Zeitpunkt abzüglich der Dauer jetzt ist.
    Um etwas Puffer zu haben, werden bei Überschreiten des Zeitpunkts die nachfolgenden 20 Min auch noch als Ladezeit
    zurückgegeben.

    Return
    ------
    neg: Zeitpunkt vorbei
    pos: verbleibende Sekunden
    """

    now = datetime.datetime.today()
    end = datetime.datetime.strptime(plan.time, '%H:%M')
    remaining_time = None
    if plan.frequency.selected == "once":
        endDate = datetime.datetime.strptime(plan.frequency.once[0], "%Y-%m-%d")
        end = end.replace(endDate.year, endDate.month, endDate.day)
        remaining_time = _get_remaining_time(now, duration, end)
    elif plan.frequency.selected == "daily":
        end = end.replace(now.year, now.month, now.day)
        remaining_time_today = _get_remaining_time(now, duration, end)
        remaining_time, end = check_following_days(now, duration, end, remaining_time_today, buffer)
    elif plan.frequency.selected == "weekly":
        end = end.replace(now.year, now.month, now.day)
        if plan.frequency.weekly[now.weekday()]:
            remaining_time = _get_remaining_time(now, duration, end)
        # prüfen, ob für den nächsten Tag ein Termin ansteht und heute schon begonnen werden muss
        if all(day == 0 for day in plan.frequency.weekly):
            raise ValueError("Es muss mindestens ein Tag ausgewählt werden.")
        num_of_following_days = _get_next_charging_day(plan.frequency.weekly, now.weekday())
        remaining_time, end = check_following_days(now, duration, end, remaining_time, buffer, num_of_following_days)
    else:
        raise TypeError(f'Unbekannte Häufigkeit {plan.frequency.selected}')
    return remaining_time, _missed_date_today(now, end, buffer)


def _get_next_charging_day(weekly_temp: List[bool], weekday: int) -> int:
    weekly_temp[weekday] = False
    try:
        return (weekly_temp[weekday:] + weekly_temp[:weekday]).index(True)
    except ValueError:
        # Es wird nur am Wochentag von weekday geladen.
        return 7


def _missed_date_today(now: datetime.datetime,
                       end: datetime.datetime,
                       buffer: float):
    return end < now + datetime.timedelta(seconds=buffer)


def check_following_days(now: datetime.datetime,
                         duration: float,
                         end: datetime.datetime,
                         remaining_time_today: Optional[float],
                         buffer: float,
                         num_of_following_days: int = 1) -> Tuple[Optional[float], datetime.datetime]:
    # Zeitpunkt heute darf noch nicht verstrichen sein
    if remaining_time_today and not _missed_date_today(now, end, buffer):
        return remaining_time_today, end
    end = end+datetime.timedelta(days=num_of_following_days)
    remaining_time = _get_remaining_time(now, duration, end)
    return remaining_time, end


def _get_remaining_time(now: datetime.datetime, duration: float, end: datetime.datetime) -> float:
    """ Return
    ------
    neg: Zeitpunkt vorbei
    pos: verbleibende Sekunden
    """
    delta = datetime.timedelta(hours=int(duration), minutes=((duration % 1) * 60))
    start_time = end-delta
    return (start_time-now).total_seconds()


def is_list_valid(hour_list: List[int]) -> bool:
    """ prüft, ob eine der angegebenen Unix-Zeiten aktuell ist.

    Parameter
    ---------
    hour_list: list
        Liste mit Unix-Zeiten

    Return
    ------
    True: aktuelle Stunde ist in der Liste enthalten
    False: aktuelle Stunde ist nicht in der Liste enthalten
    """
    try:
        now = datetime.datetime.today()
        for hour in hour_list:
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


def get_difference_to_now(timestamp_begin: str) -> Tuple[str, int]:
    """ ermittelt den Abstand zwischen zwei Zeitstempeln.

    Parameter
    ---------
    timestamp_begin: str %m/%d/%Y, %H:%M:%S
        Anfangszeitpunkt

    Return
    ------
    diff: [str, int]
        str: Differenz HH:MM, ggf DD days, HH:MM
        int: Differenz in Sekunden
    """
    try:
        begin = datetime.datetime.strptime(timestamp_begin[:-3], "%m/%d/%Y, %H:%M")
        now = datetime.datetime.today()
        diff = (now - begin)
        return [__convert_timedelta_to_time_string(diff), int(diff.total_seconds())]
    except Exception:
        log.exception("Fehler im System-Modul")
        return ["00:00", 0]


def get_difference(timestamp_begin: str, timestamp_end: str) -> Optional[int]:
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
        return int(diff.total_seconds())
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
        return __convert_timedelta_to_time_string(sum)
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


def __convert_timedelta_to_time_string(timedelta_obj: datetime.timedelta) -> str:
    diff_hours = int(timedelta_obj.total_seconds() / 3600)
    diff_minutes = int((timedelta_obj.total_seconds() % 3600) / 60)
    return f"{diff_hours}:{diff_minutes:02d}"
