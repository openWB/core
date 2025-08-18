from dataclasses import dataclass, field
import datetime
from typing import List, Optional


def once_period_factory() -> List:
    return [datetime.datetime.today().strftime("%Y-%m-%d"), datetime.datetime.today().strftime("%Y-%m-%d")]


def once_date_factory() -> List:
    return datetime.datetime.today().strftime("%Y-%m-%d")


def weekly_factory() -> List:
    return [False]*7


def time_factory():
    return ["06:00", "07:00"]


@dataclass
class Limit:
    selected: str = "none"
    amount: int = 1000
    soc: int = 50


def limit_factory() -> Limit:
    return Limit()


@dataclass
class FrequencyPeriod:
    selected: str = "daily"
    once: List[str] = field(default_factory=once_period_factory)
    weekly: List[bool] = field(default_factory=weekly_factory)


def frequency_period_factory() -> FrequencyPeriod:
    return FrequencyPeriod()


@dataclass
class FrequencyDate:
    selected: str = "daily"
    once: str = field(default_factory=once_date_factory)
    weekly: List[bool] = field(default_factory=weekly_factory)


def frequency_date_factory() -> FrequencyDate:
    return FrequencyDate()


@dataclass
class ScheduledLimit:
    selected: str = "amount"
    amount: int = 1000
    soc_limit: int = 90
    soc_scheduled: int = 80


def scheduled_limit_factory() -> ScheduledLimit:
    return ScheduledLimit()


@dataclass
class PlanBase:
    active: bool = True


@dataclass
class TimeframePlan(PlanBase):
    time: List[str] = field(default_factory=time_factory)  # ToDo: aktuelle Zeit verwenden + 1 Stunde
    frequency: FrequencyPeriod = field(default_factory=frequency_period_factory)


@dataclass
class ScheduledChargingPlan(PlanBase):
    bidi_charging_enabled: bool = False
    bidi_power: int = 10000
    current: int = 14
    dc_current: float = 145
    et_active: bool = False
    frequency: FrequencyDate = field(default_factory=frequency_date_factory)
    id: Optional[int] = None
    name: str = "neuer Zielladen-Plan"
    limit: ScheduledLimit = field(default_factory=scheduled_limit_factory)
    phases_to_use: int = 0
    phases_to_use_pv: int = 0
    time: str = "07:00"  # ToDo: aktuelle Zeit verwenden


@dataclass
class TimeChargingPlan(TimeframePlan):
    current: int = 16
    dc_current: float = 145
    id: Optional[int] = None
    limit: Limit = field(default_factory=limit_factory)
    name: str = "neuer Zeitladen-Plan"
    phases_to_use: int = 1


@dataclass
class AutolockPlan(TimeframePlan):
    id: Optional[int] = None
    name: str = "neuer Plan für Sperren nach Uhrzeit"
