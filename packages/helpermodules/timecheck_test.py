import datetime
from typing import List, Optional, Union
from unittest.mock import MagicMock, Mock
import pytest

from control.ev.charge_template import ChargeTemplate
from helpermodules import timecheck
from helpermodules.abstract_plans import AutolockPlan, Frequency, ScheduledChargingPlan, TimeChargingPlan


class Params:
    def __init__(self, name: str,
                 first_time: str,
                 expected_return: Union[int, str],
                 second_time: Optional[str] = "") -> None:
        self.name = name
        self.first_time = first_time
        self.expected_return = expected_return
        if second_time:
            self.second_time = second_time


@pytest.mark.parametrize("begin_hour, begin_min, end_hour, end_min,expected",
                         [pytest.param(0, 0, 5, 5, 9300, id="too early"),
                          pytest.param(8, 18, 10, 35, -780, id="start"),
                          pytest.param(18, 8, 17, 24, -11640, id="missed date")
                          ])
def test_get_remaining_time(begin_hour: int, begin_min: int, end_hour: int, end_min: int, expected: int):
    # setup
    end = datetime.datetime(2022, 9, 26, end_hour, end_min)
    begin = datetime.datetime(2022, 9, 26, begin_hour, begin_min)

    # execution
    diff = timecheck._get_remaining_time(begin, 9000, end)

    # evaluation
    assert expected == diff


@pytest.mark.parametrize("time, selected, date, expected",
                         [pytest.param("9:00", "once", "2022-05-16", (-7852.0, False), id="once"),
                          pytest.param("8:00", "once", "2022-05-16", (-11452.0, True), id="once missed date"),
                          pytest.param("12:00", "daily", [], (2948.0, False), id="daily today"),
                          pytest.param("2:00", "daily", [], (53348.0, False), id="daily  missed today, use next day"),
                          pytest.param("8:05", "weekly", [True, False, False, False,
                                       False, False, False], (593648.0, False), id="weekly missed today"),
                          pytest.param("2:00", "weekly", [False, False, True, False, False, False, False],
                          (139748.0, False),
                             id="weekly missed today's date, no date on next day"),
                          pytest.param("2:00", "weekly", [True, True, False, False, False, False, False],
                          (53348.0, False),
                             id="weekly missed today's date, date on next day"),
                          ]
                         )
def test_check_duration(time: str, selected: str, date: List, expected: float):
    # setup
    plan = Mock(spec=ScheduledChargingPlan, time=time, frequency=Mock(spec=Frequency, selected=selected,))
    if date:
        setattr(plan.frequency, selected, date)

    # execution
    remaining_time, missed_date_today = timecheck.check_duration(plan, 9000, ChargeTemplate.BUFFER)

    # evaluation
    assert (remaining_time, missed_date_today) == expected


@pytest.mark.parametrize("weekday, weekly, expected_days",
                         [pytest.param(0, [True, True, False, False, False, False, False], 1),
                          pytest.param(0, [True, False, False, False, False, False, False], 7),
                          pytest.param(3, [True, False, False, False, False, False, False], 4),
                          ]
                         )
def test_get_next_charging_day(weekday: int, weekly: List[bool], expected_days: int):
    # setup and execution
    days = timecheck._get_next_charging_day(weekly, weekday)

    # evaluation
    assert days == expected_days


@pytest.mark.parametrize("now, end, expected_missed",
                         [pytest.param(datetime.datetime(2022, 9, 29, 8, 40),
                                       datetime.datetime(2022, 9, 29, 9, 5), False),
                          pytest.param(datetime.datetime(2022, 9, 29, 8, 40),
                                       datetime.datetime(2022, 9, 29, 8, 39), False),
                          pytest.param(datetime.datetime(2022, 9, 29, 8, 40),
                                       datetime.datetime(2022, 9, 29, 8, 19), True)
                          ]
                         )
def test_missed_date_today(now: datetime.datetime, end: datetime.datetime, expected_missed: bool):
    # setup and execution
    missed = timecheck._missed_date_today(now, end, -1200)

    # evaluation
    assert missed == expected_missed


@pytest.mark.parametrize(
    "plan, now, expected_state",
    [pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=Frequency(selected="once", once=["2022-05-16", "2022-05-16"])),
                  "2022-05-16 9:50", False, id="once, 10-12 at 9.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=Frequency(selected="once", once=["2022-05-16", "2022-05-16"])),
                  "2022-05-16 10:50", True, id="once, 10-12 at 10.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=Frequency(selected="once", once=["2022-05-16", "2022-05-16"])),
                  "2022-05-16 13:50", False, id="once, 10-12 at 13.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"], frequency=Frequency(selected="daily")),
                  "2022-05-16 11:50", True, id="daily, 10-12 at 11.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"], frequency=Frequency(selected="daily")),
                  "2022-05-16 22:50", True, id="daily, 22-02 at 22.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"], frequency=Frequency(selected="daily")),
                  "2022-05-17 1:50", True, id="daily, 22-02 at 1.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"], frequency=Frequency(selected="daily")),
                  "2022-05-17 2:50", False, id="daily, 22-02 at 2.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=Frequency(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-16 10:50", True, id="weekly, 10-12 at 10.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=Frequency(selected="weekly", weekly=[0, 1, 0, 0, 0, 0, 0])),
                  "2022-05-16 10:50", False, id="weekly, 10-12 at 10.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=Frequency(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-16 22:50", True, id="weekly, 22-02 at 22.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=Frequency(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-17 1:50", True, id="weekly, 22-02 at 1.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=Frequency(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-16 1:50", False, id="weekly, 22-02 at 1.50, weekday before"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=Frequency(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-18 1:50", False, id="weekly, 22-02 at 1.50, weekday after"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=Frequency(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-17 2:50", False, id="weekly, 22-02 at 2.50"),
     ]
)
def test_check_timeframe(plan: Union[AutolockPlan, TimeChargingPlan], now: str, expected_state: bool, monkeypatch):
    # setup
    datetime_mock = MagicMock(wraps=datetime.datetime)
    datetime_mock.today.return_value = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M")
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    # execution
    state = timecheck.check_timeframe(plan)

    # evaluation
    assert state == expected_state


@pytest.mark.parametrize("timestamp, expected",
                         [
                             pytest.param(1652683202, "40 Sek."),
                             pytest.param(1652683222, "1 Min."),
                             pytest.param(1652683221.8, "59 Sek."),
                             pytest.param(1652683222.2, "1 Min."),
                             pytest.param(1652683232, "1 Min. 10 Sek.")
                         ]
                         )
def test_convert_timestamp_delta_to_time_string(timestamp, expected):
    # setup
    delta = 90

    # execution
    time_string = timecheck.convert_timestamp_delta_to_time_string(timestamp, delta)

    # evaluation
    assert time_string == expected
