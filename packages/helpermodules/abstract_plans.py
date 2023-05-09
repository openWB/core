from dataclasses import dataclass, field
from typing import List


def once_factory() -> List:
    return ["2021-11-01", "2021-11-05"]  # ToDo: aktuelles Datum verwenden


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
class Frequency:
    selected: str = "daily"
    once: List[str] = field(default_factory=once_factory)
    weekly: List[bool] = field(default_factory=weekly_factory)


def frequency_factory() -> Frequency:
    return Frequency()


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
    active: bool = False
    frequency: Frequency = field(default_factory=frequency_factory)


@dataclass
class TimeframePlan(PlanBase):
    time: List[str] = field(default_factory=time_factory)  # ToDo: aktuelle Zeit verwenden + 1 Stunde


@dataclass
class ScheduledChargingPlan(PlanBase):
    current: int = 14
    name: str = "Zielladen-Standard"
    limit: ScheduledLimit = field(default_factory=scheduled_limit_factory)
    time: str = "07:00"  # ToDo: aktuelle Zeit verwenden


@dataclass
class TimeChargingPlan(TimeframePlan):
    name: str = "Zeitladen-Standard"
    current: int = 16
    limit: Limit = field(default_factory=limit_factory)


@dataclass
class AutolockPlan(TimeframePlan):
    name: str = "Standard Autolock-Plan"
