from dataclasses import dataclass, field
from typing import List


def once_factory() -> List:
    return ["2021-11-01", "2021-11-05"]  # ToDo: aktuelles Datum verwenden


def weekly_factory() -> List:
    return [False, False, False, False, False, False, False]


def time_factory():
    return ["06:00", "07:00"]


@dataclass
class Frequency:
    selected: str = "daily"
    once: List[str] = field(default_factory=once_factory)
    weekly: List[bool] = field(default_factory=weekly_factory)


def frequency_factory() -> Frequency:
    return Frequency()


@dataclass
class Limit:
    selected: str = "none"
    soc: int = 50
    amount: int = 1000


def limit_factory() -> Limit:
    return Limit()


@dataclass
class ScheduledChargingPlan:
    name: str = "Zielladen-Standard"
    active: bool = False
    time: str = "07:00"  # ToDo: aktuelle Zeit verwenden
    limit: Limit = field(default_factory=limit_factory)
    frequency: Frequency = field(default_factory=frequency_factory)


@dataclass
class TimeChargingPlan:
    name: str = "Zeitladen-Standard"
    active: bool = False
    time: List[str] = field(default_factory=time_factory)  # ToDo: aktuelle Zeit verwenden + 1 Stunde
    current: int = 16
    frequency: Frequency = field(default_factory=frequency_factory)
