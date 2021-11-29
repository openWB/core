from datetime import datetime
from typing import List

import pytest as pytest

from .chargepoint import cpTemplate
from modules.testutils.mock import ignore_logging


class Params:
    def __init__(
            self, name: str, data: dict, autolock_state: int, charge_state: bool, time: list, expected_state: int,
            weekly: List = None, once: List = None):
        self.name = name
        self.data = data
        self.data["autolock"]["plans"]["0"]["time"] = time
        if weekly is not None:
            self.data["autolock"]["plans"]["0"]["frequency"]["weekly"] = weekly
        if once is not None:
            self.data["autolock"]["plans"]["0"]["frequency"]["once"] = once
        self.autolock_state = autolock_state
        self.charge_state = charge_state
        self.expected_state = expected_state


now = datetime.today()
if now.hour + 1 > 24 or now.hour - 1 < 0:
    assert "Test funktioniert nur tagsüber"
time_before = [str(now.hour+1)+":"+str(now.minute), str(now.hour+2)+":"+str(now.minute)]
time_during = [str(now.hour-1)+":"+str(now.minute), str(now.hour+1)+":"+str(now.minute)]
time_after = [str(now.hour-2)+":"+str(now.minute), str(now.hour-1)+":"+str(now.minute)]

weekly_none = [False]*7
weekly_all = [True]*7

once_before = [str(now.day+1), str(now.day+2)]
once_during = [str(now.day-1), str(now.day+1)]
once_after = [str(now.day-2), str(now.day-1)]

data_daily_not_wait_for_end = {"autolock": {
    "wait_for_charging_end": False,
    "active": True,
    "plans": {"0": {"name": "Standard Autolock-Plan",
                            "frequency":
                            {
                                "selected": "daily"
                            },
                    "active": True}}}}
data_daily_wait_for_end = {"autolock": {
    "wait_for_charging_end": True,
    "active": True,
    "plans": {"0": {"name": "Standard Autolock-Plan",
                            "frequency":
                            {
                                "selected": "daily"
                            },
                    "active": True}}}}
data_weekly_not_wait_for_end = {"autolock": {
    "wait_for_charging_end": False,
    "active": True,
    "plans": {"0": {"name": "Standard Autolock-Plan",
                            "frequency":
                            {
                                "selected": "weekly",
                                "weekly": [True, False, False, False, False, False, False, False]
                            },
                    "active": True}}}}
data_once_not_wait_for_end = {"autolock": {
    "wait_for_charging_end": False,
    "active": True,
    "plans": {"0": {"name": "Standard Autolock-Plan",
                            "frequency":
                            {
                                "selected": "once",
                                "once": ["02.11.2021", "05.11.2021"]
                            },
                    "active": True}}}}

cases = [
    Params(name="Daily, Don't wait for charging end, Current-Time before Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_before, expected_state=True),
    Params(name="Daily, Don't wait for charging end, Current-Time during Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_during, expected_state=False),
    Params(name="Daily, Don't wait for charging end, Current-Time after Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_after, expected_state=True),

    Params(name="Daily, Wait for charging end, Current-Time after Lock, still charging:",
           data=data_daily_wait_for_end,
           autolock_state=0, charge_state=True, time=time_after, expected_state=False),
    Params(name="Daily, Wait for charging end, Current-Time after Lock, ended charging:",
           data=data_daily_wait_for_end,
           autolock_state=0, charge_state=False, time=time_after, expected_state=True),

    Params(name="Autolock inactive",
           data={"autolock": {
               "wait_for_charging_end": False,
               "active": False,
               "plans": {"0": {"name": "Standard Autolock-Plan",
                               "frequency":
                               {
                                   "selected": "daily"
                               },
                               "time": ["12:00", "16:00"],
                               "active": True}}}},
           autolock_state=0, charge_state=True, time=time_after, expected_state=False),

    Params(name="Weekly, not current day, Don't wait for charging end, Current-Time before Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_before, expected_state=False, weekly=weekly_none),
    Params(name="Weekly, not current day, Don't wait for charging end, Current-Time during Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_during, expected_state=False, weekly=weekly_none),
    Params(name="Weekly, not current day, Don't wait for charging end, Current-Time after Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_after, expected_state=False, weekly=weekly_none),

    Params(name="Weekly, current day, Don't wait for charging end, Current-Time before Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_before, expected_state=False, weekly=weekly_all),
    Params(name="Weekly, current day, Don't wait for charging end, Current-Time during Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_during, expected_state=False, weekly=weekly_all),
    Params(name="Weekly, current day, Don't wait for charging end, Current-Time after Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_after, expected_state=False, weekly=weekly_all),

    Params(name="Once, before period, Don't wait for charging end, Current-Time before Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_before, expected_state=False),
    Params(name="Once, after period, Don't wait for charging end, Current-Time before Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_before, expected_state=False),
    Params(name="Once, during period, Don't wait for charging end, Current-Time before Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_before, expected_state=False),
    Params(name="Once, during period, Don't wait for charging end, Current-Time during Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_during, expected_state=False),
    Params(name="Once, during period, Don't wait for charging end, Current-Time after Lock:",
           data=data_daily_not_wait_for_end,
           autolock_state=0, charge_state=True, time=time_after, expected_state=False),

]


@pytest.mark.parametrize("params", cases, ids=[c.name for c in cases])
def test_autolock_state(params: Params, monkeypatch):
    # setup
    ignore_logging(monkeypatch)

    # execution
    cpt = cpTemplate()
    cpt.data = params.data
    actual = cpt.autolock(
        params.autolock_state, params.charge_state, 0)

    # evaluation
    assert actual == params.expected_state
