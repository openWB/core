import datetime
from typing import List, Optional, Union
from unittest.mock import MagicMock, Mock
import pytest

from control.ev import ChargeTemplate
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


# cases_get_difference_to_now = [
#     Params("get_difference_to_now_minutes_before", "02/18/2022, 10:42:23", expected_return="87"),
#     Params("get_difference_to_now_minutes_after", "02/18/2022, 10:50:45",  expected_return="469"),
#     Params("get_difference_to_now_hours", "02/18/2022, 10:42:56",  expected_return="8651"),
#     Params("get_difference_to_now_days", "02/16/2022, 08:18:45", expected_return="164149"),
# ]
cases_get_difference = [
    Params("get_difference_minutes_before", "02/18/2022, 10:42:23",
           second_time="02/18/2022, 10:40:56", expected_return=87),
    Params("get_difference_minutes_after", "02/18/2022, 10:50:45",
           second_time="02/18/2022, 10:42:56", expected_return=469),
    Params("get_difference_hours", "02/18/2022, 10:42:56", second_time="02/18/2022, 08:18:45", expected_return=8651),
    Params("get_difference_days", "02/18/2022, 08:18:45", second_time="02/16/2022, 10:42:56", expected_return=164149),
]

cases_duration_sum = [
    Params("duration_sum_minutes", "00:23", second_time="00:56", expected_return="1:19"),
    Params("duration_sum_hours", "08:18", second_time="01:56", expected_return="10:14"),
    Params("duration_sum_days", "18:8", second_time="10:24", expected_return="28:32"),
]

# @pytest.fixture(autouse=True)
# def set_up(monkeypatch):
#     mock_today = Mock(name="today", return_value="02/18/2022, 10:42")
#     monkeypatch.setattr(datetime, "today", mock_today)


@pytest.mark.parametrize("params", cases_get_difference, ids=[c.name for c in cases_get_difference])
def test_get_difference(params: Params):
    # execution
    diff = timecheck.get_difference(params.first_time, params.second_time)

    # evaluation
    assert params.expected_return == diff


@pytest.mark.parametrize("params", cases_duration_sum, ids=[c.name for c in cases_duration_sum])
def test_duration_sum(params: Params):
    # execution
    diff = timecheck.duration_sum(params.first_time, params.second_time)

    # evaluation
    assert params.expected_return == diff


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
    diff = timecheck._get_remaining_time(begin, 2.5, end)

    # evaluation
    assert expected == diff


@pytest.mark.parametrize("time, selected, date, expected",
                         [pytest.param("9:00", "once", ["2022-05-16", ], (-7852.0, False), id="once"),
                          pytest.param("8:00", "once", ["2022-05-16", ], (-11452.0, True), id="once missed date"),
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
    remaining_time, missed_date_today = timecheck.check_duration(plan, 2.5, ChargeTemplate.BUFFER)

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


def test_convert_to_unix_timestamp():
    # setup and execution
    unix_timestamp = timecheck.convert_to_unix_timestamp("10/31/2022, 07:00:00")

    # evaluation
    assert unix_timestamp == 1667196000
