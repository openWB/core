import datetime
import logging
from typing import List, Optional, Union
from unittest.mock import MagicMock, Mock
import pytest

from helpermodules import timecheck
from helpermodules.abstract_plans import (AutolockPlan, FrequencyDate, FrequencyPeriod, ScheduledChargingPlan,
                                          TimeChargingPlan)

log = logging.getLogger(__name__)


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


@pytest.mark.parametrize("time, selected, date, expected_remaining_time",
                         [pytest.param("9:00", "once", "2022-05-16", 1148, id="once"),
                          pytest.param("7:55", "once", "2022-05-16", None, id="missed date, plugged before"),
                          pytest.param("8:05", "once", "2022-05-16", -
                                       2152, id="once missed date, plugged after"),
                          pytest.param("12:00", "daily", [], 11948, id="daily today"),
                          pytest.param("2:00", "daily", [], 62348, id="daily  missed today, use next day"),
                          pytest.param("7:55", "weekly", [True, False, False, False,
                                       False, False, False], 602048, id="weekly missed today"),
                          pytest.param("2:00", "weekly", [False, False, True, False, False, False, False],
                          148748, id="weekly missed today's date, no date on next day"),
                          pytest.param("2:00", "weekly", [True, True, False, False, False, False, False],
                          62348, id="weekly missed today's date, date on next day"),
                          ]
                         )
def test_check_end_time(time: str,
                        selected: str,
                        date: List,
                        expected_remaining_time: float):
    # setup
    plan = Mock(spec=ScheduledChargingPlan, time=time, frequency=Mock(spec=FrequencyDate, selected=selected,))
    if date:
        setattr(plan.frequency, selected, date)

    # execution
    remaining_time = timecheck.check_end_time(
        plan,
        chargemode_switch_timestamp=datetime.datetime.strptime("5/16/2022 8:00", "%m/%d/%Y %H:%M").timestamp())

    # evaluation
    assert remaining_time == expected_remaining_time


@pytest.mark.parametrize("weekday, weekly, expected_days",
                         [pytest.param(0, [True, True, False, False, False, False, False], 0),
                          pytest.param(1, [True, False, False, False, False, False, False], 6),
                          pytest.param(3, [True, False, False, False, False, False, False], 4),
                          ]
                         )
def test_get_next_charging_day(weekday: int, weekly: List[bool], expected_days: int):
    # setup and execution
    days = timecheck._get_next_charging_day(weekly, weekday)

    # evaluation
    assert days == expected_days


@pytest.mark.parametrize(
    "plan, now, expected_state",
    [pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=FrequencyPeriod(selected="once", once=["2022-05-16", "2022-05-16"])),
                  "2022-05-16 9:50", False, id="once, 10-12 at 9.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=FrequencyPeriod(selected="once", once=["2022-05-16", "2022-05-16"])),
                  "2022-05-16 10:50", True, id="once, 10-12 at 10.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=FrequencyPeriod(selected="once", once=["2022-05-16", "2022-05-16"])),
                  "2022-05-16 13:50", False, id="once, 10-12 at 13.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"], frequency=FrequencyPeriod(selected="daily")),
                  "2022-05-16 11:50", True, id="daily, 10-12 at 11.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"], frequency=FrequencyPeriod(selected="daily")),
                  "2022-05-16 22:50", True, id="daily, 22-02 at 22.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"], frequency=FrequencyPeriod(selected="daily")),
                  "2022-05-17 1:50", True, id="daily, 22-02 at 1.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"], frequency=FrequencyPeriod(selected="daily")),
                  "2022-05-17 2:50", False, id="daily, 22-02 at 2.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-16 10:50", True, id="weekly, 10-12 at 10.50"),
     pytest.param(TimeChargingPlan(active=True, time=["10:00", "12:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[0, 1, 0, 0, 0, 0, 0])),
                  "2022-05-16 10:50", False, id="weekly, 10-12 at 10.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-16 22:50", True, id="weekly, 22-02 at 22.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-17 1:50", True, id="weekly, 22-02 at 1.50"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-16 1:50", False, id="weekly, 22-02 at 1.50, weekday before"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
                  "2022-05-18 1:50", False, id="weekly, 22-02 at 1.50, weekday after"),
     pytest.param(TimeChargingPlan(active=True, time=["22:00", "2:00"],
                                   frequency=FrequencyPeriod(selected="weekly", weekly=[1, 0, 0, 0, 0, 0, 0])),
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


@pytest.mark.parametrize("timestamp, expected",
                         [
                             pytest.param("2025-10-01 09:00", "2025-10-01 09:00", id="9:00"),
                             pytest.param("2025-10-01 09:01", "2025-10-01 09:00", id="9:01"),
                             pytest.param("2025-10-01 09:10", "2025-10-01 09:00", id="9:10"),
                             pytest.param("2025-10-01 09:14", "2025-10-01 09:00", id="9:14"),
                             pytest.param("2025-10-01 09:15", "2025-10-01 09:15", id="9:15"),
                             pytest.param("2025-10-01 09:41", "2025-10-01 09:30", id="9:41"),
                             pytest.param("2025-10-01 09:46", "2025-10-01 09:45", id="9:46")
                         ]
                         )
def test_create_unix_timestamp_current_quarter_hour(timestamp, expected, monkeypatch):
    # setup
    datetime_mock = MagicMock(wraps=datetime.datetime)
    current_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
    datetime_mock.today.return_value = current_time
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    # execution
    qh = timecheck.create_unix_timestamp_current_quarter_hour()
    log.debug(f"timestamp: {current_time} , from mock: {datetime.datetime.today().timestamp()}"
              f" result:  {qh}")

    current_quarter_hour = datetime.datetime.fromtimestamp(qh).strftime("%Y-%m-%d %H:%M")

    # evaluation
    assert current_quarter_hour == expected
