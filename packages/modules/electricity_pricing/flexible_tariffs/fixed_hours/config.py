from dataclasses import dataclass, field
from typing import Any


@dataclass
class FixedHoursTariffConfiguration:
    '''
    Example configuration:
    "tariffs": [
        {
            "name": "high_tariff",
            "price": 0.20,
            "active_times": {
                "dates": [("01-01", "31-03"), ("01-07", "30-09")],  # applicable date ranges (day-month)
                "weekdays": [0, 1, 2, 3, 4],  # active on weekdays (0=Monday, ..., 6=Sunday)
                "times": [("08:00", "12:00"), ("18:00", "22:00")]  # active times during the day
            }
        },
        {
            "name": "low_tariff",
            "price": 0.05,
            "active_times": {
                "dates": [("01-04", "30-06"), ("01-10", "31-12")],  # applicable date ranges (day-month)
                "weekdays": [5, 6],  # active on weekends (0=Monday, ..., 6=Sunday)
                "times": [("00:00", "06:00"), ("22:00", "23:59")]  # active times during the day
            }
        }
    ]
    '''
    default_price: float = 0
    tariffs: list[dict[str, Any]] = field(default_factory=list)
    update_hours: list[int] = field(default_factory=lambda: list(range(24)))


@dataclass
class FixedHoursTariff:
    name: str = "Feste Tarifstunden (z.b. §14a EnWG Modul3)"
    type: str = "fixed_hours"
    official: bool = False
    configuration: FixedHoursTariffConfiguration = field(default_factory=FixedHoursTariffConfiguration)
