"""prüft, ob Zeitfenster aktuell sind
"""
import logging
import datetime
import re
from typing import List, Optional, Tuple, TypeVar, Union

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from dateutil.relativedelta import relativedelta

from helpermodules.abstract_plans import (AutolockPlan, ScheduledChargingPlan, ScheduledPlanConsumer,
                                          TimeChargingPlan, TimeChargingPlanConsumer)

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


T = TypeVar("T", AutolockPlan, TimeChargingPlan, TimeChargingPlanConsumer)


def _parse_plan_time(time_value: str) -> Tuple[int, int]:
    parsed_time = datetime.datetime.strptime(time_value, "%H:%M")
    return parsed_time.hour, parsed_time.minute


def _is_timeframe_valid(now: datetime.datetime, begin: datetime.datetime, end: datetime.datetime) -> bool:
    return (not now < begin) and now < end


def _is_weekday_enabled(weekly: List[bool], weekday: int) -> bool:
    return weekly[weekday % 7]


def check_plans_timeframe(plans: List[T]) -> Optional[T]:
    """ gibt den ersten aktiven Plan zurück. None, falls kein Plan aktiv ist.
    """
    state = False
    try:
        for plan in plans:
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
    state = False
    try:
        now = datetime.datetime.today()
        begin_hour, begin_minute = _parse_plan_time(plan.time[0])
        end_hour, end_minute = _parse_plan_time(plan.time[1])

        if plan.frequency.selected == "once":
            begin_date = datetime.datetime.strptime(plan.frequency.once[0], "%Y-%m-%d")
            begin = now.replace(
                year=begin_date.year,
                month=begin_date.month,
                day=begin_date.day,
                hour=begin_hour,
                minute=begin_minute,
                second=0,
                microsecond=0,
            )
            end_date = datetime.datetime.strptime(plan.frequency.once[1], "%Y-%m-%d")
            end = now.replace(
                year=end_date.year,
                month=end_date.month,
                day=end_date.day,
                hour=end_hour,
                minute=end_minute,
                second=0,
                microsecond=0,
            )
            state = _is_timeframe_valid(now, begin, end)

        else:
            begin = now.replace(hour=begin_hour, minute=begin_minute, second=0, microsecond=0)
            end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            day_change = begin > end
            if day_change:
                # Endzeit ist am nächsten Tag, in Zeitabschnitt vor und nach Mitternacht einteilen
                next_day = now + datetime.timedelta(days=1)
                next_day_midnight = next_day.replace(hour=0, minute=0)
                state_after_midnight = _is_timeframe_valid(now, begin, next_day_midnight)
                state_before_midnight = _is_timeframe_valid(now, now.replace(hour=0, minute=0), end)

            if plan.frequency.selected == "daily":
                if day_change:
                    state = state_before_midnight or state_after_midnight
                else:
                    state = _is_timeframe_valid(now, begin, end)

            elif plan.frequency.selected == "weekly":
                if day_change:
                    state = ((state_after_midnight and _is_weekday_enabled(plan.frequency.weekly, now.weekday())) or
                             (state_before_midnight and _is_weekday_enabled(plan.frequency.weekly, now.weekday() - 1)))
                else:
                    if _is_weekday_enabled(plan.frequency.weekly, now.weekday()):
                        state = _is_timeframe_valid(now, begin, end)
    except Exception:
        log.exception("Fehler im System-Modul")
    finally:
        return state


def get_next_timeframe_plan_start(plans: List[T],
                                  now: Optional[datetime.datetime] = None) -> Optional[datetime.datetime]:
    if now is None:
        now = datetime.datetime.today()

    next_starts: List[datetime.datetime] = []
    for plan in plans:
        if not getattr(plan, "active", False):
            continue
        try:
            next_start = _get_next_start_for_timeframe_plan(plan, now)
            if next_start is not None:
                next_starts.append(next_start)
        except Exception:
            log.exception("Fehler im System-Modul")

    if not next_starts:
        return None
    return min(next_starts)


def _get_next_start_for_timeframe_plan(plan: T, now: datetime.datetime) -> Optional[datetime.datetime]:
    start_hour, start_minute = _parse_plan_time(plan.time[0])

    if plan.frequency.selected == "once":
        begin_date = datetime.datetime.strptime(plan.frequency.once[0], "%Y-%m-%d")
        next_start = now.replace(
            year=begin_date.year,
            month=begin_date.month,
            day=begin_date.day,
            hour=start_hour,
            minute=start_minute,
            second=0,
            microsecond=0,
        )
        return next_start if next_start > now else None

    if plan.frequency.selected == "daily":
        next_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        if next_start <= now:
            next_start += datetime.timedelta(days=1)
        return next_start

    if plan.frequency.selected == "weekly":
        if not any(plan.frequency.weekly):
            return None
        for day_offset in range(0, 8):
            weekday = (now.weekday() + day_offset) % 7
            if not plan.frequency.weekly[weekday]:
                continue
            candidate = (now + datetime.timedelta(days=day_offset)).replace(
                hour=start_hour,
                minute=start_minute,
                second=0,
                microsecond=0,
            )
            if candidate > now:
                return candidate
    return None


def check_end_time(plan: Union[ScheduledPlanConsumer, ScheduledChargingPlan, TimeChargingPlanConsumer],
                   buffer: Optional[float]) -> float:
    """ gibt die verbleibende Zeit in Sekunden zurück.

    Return
    ------
    neg: Zeitpunkt vorbei
    pos: verbleibende Sekunden
    """
    now = datetime.datetime.today()
    end = datetime.datetime.strptime(plan.time, '%H:%M')
    if plan.frequency.selected == "once":
        endDate = datetime.datetime.strptime(plan.frequency.once, "%Y-%m-%d")
        end = end.replace(endDate.year, endDate.month, endDate.day)
        remaining_time = end - now
    elif plan.frequency.selected == "daily":
        end = end.replace(now.year, now.month, now.day)
        remaining_time = end - now
        if remaining_time.total_seconds() < buffer:
            # Wenn auf Zielladen umgeschaltet wurde und der Termin noch nicht vorbei war, noch auf diesen Termin laden.
            end = end + datetime.timedelta(days=1)
            remaining_time = end - now
    elif plan.frequency.selected == "weekly":
        if not any(plan.frequency.weekly):
            raise ValueError("Es muss mindestens ein Tag ausgewählt werden.")
        end = end.replace(now.year, now.month, now.day)
        end += datetime.timedelta(days=_get_next_charging_day(plan.frequency.weekly, now.weekday()))
        remaining_time = end - now
        if remaining_time.total_seconds() < buffer:
            end = end.replace(now.year, now.month, now.day)
            end += datetime.timedelta(days=_get_next_charging_day(plan.frequency.weekly, now.weekday()+1)+1)
            remaining_time = end - now
    else:
        raise TypeError(f'Unbekannte Häufigkeit {plan.frequency.selected}')
    return remaining_time.total_seconds()


def _get_next_charging_day(weekly: List[bool], weekday: int) -> int:
    count = 0
    for i in range(weekday, len(weekly)):
        if weekly[i] is True:
            return count
        count += 1
    for i in range(0, weekday):
        if weekly[i] is True:
            return count
        count += 1
    return count


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


def __get_timedelta_obj(time_str: str) -> datetime.timedelta:
    """ erstellt aus einem String ein timedelta-Objekt.
    Parameter
    ---------
    time_str: str
        Zeitstrings HH:MM ggf DD:HH:MM
    """
    time_charged = time_str.split(":")
    if len(time_charged) == 2:
        delta = datetime.timedelta(hours=int(time_charged[0]),
                                   minutes=int(time_charged[1]))
    elif len(time_charged) == 3:
        delta = datetime.timedelta(days=int(time_charged[0]),
                                   hours=int(time_charged[1]),
                                   minutes=int(time_charged[2]))
    else:
        raise Exception(f"Unknown charge duration: {time_str}")
    return delta


def convert_timedelta_to_time_string(timedelta_obj: datetime.timedelta) -> str:
    diff_hours = int(timedelta_obj.total_seconds() / 3600)
    diff_minutes = int((timedelta_obj.total_seconds() % 3600) / 60)
    return f"{diff_hours}:{diff_minutes:02d}"


def convert_timestamp_delta_to_time_string(timestamp: int, delta: int) -> str:
    diff = int(delta - (create_timestamp() - timestamp))
    seconds_diff = diff % 60
    minute_diff = int((diff - seconds_diff) / 60)
    if minute_diff > 0 and seconds_diff > 0:
        return f"{minute_diff} Min. {seconds_diff} Sek."
    elif minute_diff > 0:
        return f"{minute_diff} Min."
    elif seconds_diff > 0:
        return f"{seconds_diff} Sek."


def convert_to_timestamp(timestring: str) -> int:
    return int(datetime.datetime.fromisoformat(timestring).timestamp())


def parse_iso8601_duration(duration: str) -> float:
    """
    Parst eine ISO-8601 Duration wie 'PT3723S', 'P1DT2H30M', etc.
    Gibt ein timedelta zurück.
    """
    pattern = re.compile(
        r'P'                      # beginnt immer mit P
        r'(?:(?P<days>\d+)D)?'    # Tage
        r'(?:T'                   # Zeit-Teil beginnt mit T
        r'(?:(?P<hours>\d+)H)?'   # Stunden
        r'(?:(?P<minutes>\d+)M)?'  # Minuten
        r'(?:(?P<seconds>\d+)S)?'  # Sekunden
        r')?$'
    )

    match = pattern.fullmatch(duration)
    if not match:
        raise ValueError(f"Ungültiges ISO-8601 Duration Format: {duration}")

    parts = {name: int(val) if val else 0 for name, val in match.groupdict().items()}
    return datetime.timedelta(days=parts["days"], hours=parts["hours"],
                              minutes=parts["minutes"], seconds=parts["seconds"]).total_seconds()
