"""prüft, ob Zeitfenster aktuell sind
"""
import copy
import logging
import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional, Tuple, TypeVar, Union

from helpermodules.abstract_plans import AutolockPlan, ScheduledChargingPlan, TimeChargingPlan

log = logging.getLogger(__name__)


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
    """ gibt den ersten aktiven Plan zurück. None, falls kein Plan aktiv ist.
    """
    state = False
    try:
        for plan in plans.values():
            if plan.active:
                state = check_timeframe(plan)
                if state:
                    return plan
        else:
            return None
    except Exception:
        log.exception("Fehler im System-Modul")
        return None


def check_timeframe(plan: Union[AutolockPlan, TimeChargingPlan]) -> bool:
    """ Returns: True -> Zeitfenster gültig, False -> Zeitfenster nicht gültig
    """
    def is_timeframe_valid(now: datetime.datetime, begin: datetime.datetime, end: datetime.datetime) -> bool:
        return True if (not now < begin) and now < end else False

    state = False
    try:
        now = datetime.datetime.today()
        begin = datetime.datetime.strptime(plan.time[0], '%H:%M')
        end = datetime.datetime.strptime(plan.time[1], '%H:%M')

        if plan.frequency.selected == "once":
            beginDate = datetime.datetime.strptime(plan.frequency.once[0], "%Y-%m-%d")
            begin = begin.replace(beginDate.year, beginDate.month, beginDate.day)
            endDate = datetime.datetime.strptime(plan.frequency.once[1], "%Y-%m-%d")
            end = end.replace(endDate.year, endDate.month, endDate.day)
            state = is_timeframe_valid(now, begin, end)

        else:
            begin = begin.replace(now.year, now.month, now.day)
            end = end.replace(now.year, now.month, now.day)
            day_change = begin > end
            if day_change:
                # Endzeit ist am nächsten Tag, in Zeitabschnitt vor und nach Mitternacht einteilen
                next_day = now + datetime.timedelta(days=1)
                next_day_midnight = next_day.replace(hour=0, minute=0)
                state_after_midnight = is_timeframe_valid(now, begin, next_day_midnight)
                state_before_midnight = is_timeframe_valid(now, now.replace(hour=0, minute=0), end)

            if plan.frequency.selected == "daily":
                if day_change:
                    state = state_before_midnight or state_after_midnight
                else:
                    state = is_timeframe_valid(now, begin, end)

            elif plan.frequency.selected == "weekly":
                if day_change:
                    state = ((state_after_midnight and plan.frequency.weekly[now.weekday()]) or
                             (state_before_midnight and plan.frequency.weekly[now.weekday() - 1]))
                else:
                    if plan.frequency.weekly[now.weekday()]:
                        state = is_timeframe_valid(now, begin, end)
    except Exception:
        log.exception("Fehler im System-Modul")
    finally:
        return state


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
        endDate = datetime.datetime.strptime(plan.frequency.once, "%Y-%m-%d")
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
        if not any(plan.frequency.weekly):
            raise ValueError("Es muss mindestens ein Tag ausgewählt werden.")
        num_of_following_days = _get_next_charging_day(copy.deepcopy(plan.frequency.weekly), now.weekday())
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
    delta = datetime.timedelta(seconds=duration)
    start_time = end-delta
    log.debug(f"delta {delta} start_time {start_time} end {end} now {now}")
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
        for hour in hour_list:
            if hour == create_unix_timestamp_current_full_hour():
                return True
        else:
            return False
    except Exception:
        log.exception("Fehler im System-Modul")
        return False


def check_timestamp(timestamp: int, duration: int) -> bool:
    """ prüft, ob der Zeitstempel innerhalb der angegebenen Zeit liegt

    Return
    ------
    True: Zeit ist noch nicht abgelaufen
    False: Zeit ist abgelaufen
    """
    if (create_timestamp() - duration) > timestamp:
        return False
    else:
        return True


def create_timestamp() -> float:
    return datetime.datetime.today().timestamp()


def create_timestamp_YYYY() -> str:
    return datetime.datetime.today().strftime("%Y")


def create_timestamp_YYYYMM() -> str:
    stamp = datetime.datetime.today().strftime("%Y%m")
    return stamp


def create_timestamp_YYYYMMDD() -> str:
    stamp = datetime.datetime.today().strftime("%Y%m%d")
    return stamp


def create_timestamp_HH_MM() -> str:
    return datetime.datetime.today().strftime("%H:%M")


def create_unix_timestamp_current_full_hour() -> int:
    full_hour = datetime.datetime.fromtimestamp(create_timestamp()).strftime("%m/%d/%Y, %H")
    return int(datetime.datetime.strptime(full_hour, "%m/%d/%Y, %H").timestamp())


def get_relative_date_string(date_string: str, day_offset: int = 0, month_offset: int = 0, year_offset: int = 0) -> str:
    print_format = "%Y%m%d" if len(date_string) > 6 else "%Y%m"
    my_date = datetime.datetime.strptime(date_string, print_format)
    return (my_date + relativedelta(years=year_offset, months=month_offset, days=day_offset)).strftime(print_format)


def get_difference_to_now(timestamp_begin: float) -> Tuple[str, int]:
    """ ermittelt den Abstand zwischen zwei Zeitstempeln.
    Return
    ------
    diff: [str, int]
        str: Differenz HH:MM, ggf DD days, HH:MM
        int: Differenz in Sekunden
    """
    try:
        diff = datetime.timedelta(seconds=create_timestamp()-timestamp_begin)
        return (convert_timedelta_to_time_string(diff), int(diff.total_seconds()))
    except Exception:
        log.exception("Fehler im System-Modul")
        return ("00:00", 0)


def get_difference(timestamp_begin: str, timestamp_end: str) -> Optional[int]:
    """ ermittelt den Abstand zwischen zwei Zeitstempeln in absoluten Sekunden.
    Parameter
    ---------
    timestamp_begin: str %m/%d/%Y, %H:%M:%S
        Anfangszeitpunkt
    timestamp_end: str %m/%d/%Y, %H:%M:%S
        Endzeitpunkt
    Return
    ------
    diff: int
        Differenz in Sekunden
    """
    try:
        begin = datetime.datetime.strptime(timestamp_begin, "%m/%d/%Y, %H:%M:%S")
        end = datetime.datetime.strptime(timestamp_end, "%m/%d/%Y, %H:%M:%S")
        diff = (end - begin)
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
        return convert_timedelta_to_time_string(sum)
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


def convert_timedelta_to_time_string(timedelta_obj: datetime.timedelta) -> str:
    diff_hours = int(timedelta_obj.total_seconds() / 3600)
    diff_minutes = int((timedelta_obj.total_seconds() % 3600) / 60)
    return f"{diff_hours}:{diff_minutes:02d}"
