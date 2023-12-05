import datetime
import json
from unittest.mock import MagicMock, Mock

import pytest
from control import data
from control.chargelog import chargelog
from control.chargelog.chargelog import (ReferenceTime, _calc, _get_reference_entry, _get_reference_position,
                                         calculate_charge_cost, get_reference_time)
from control.chargepoint.chargepoint import Chargepoint
from control.general import General
from control.optional import Optional


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Mock())
    data.data.general_data = General()
    data.data.optional_data = Optional()
    data.data.cp_data["cp3"] = Chargepoint(3, Mock)


EXPECTED_ENTRY_TODAYS_DAILY = {"timestamp": 1698880500, "date": "00:15", "cp":
                               {"cp5":
                                {"imported": 0, "exported": 0}, "cp3":
                                   {"imported": 17726.504, "exported": 0}, "cp4":
                                   {"imported": 0, "exported": 0}, "all":
                                   {"imported": 17726.504, "exported": 0}}, "ev":
                               {"ev0":
                                   {"soc": 0}}, "counter":
                               {"counter0":
                                   {"imported": 7144.779, "exported": 20.152, "grid": True}}, "pv":
                               {"all":
                                   {"exported": 11574}, "pv1":
                                   {"exported": 11574}}, "bat":
                               {"all":
                                   {"imported": 6.33, "exported": 2506.763, "soc": 0}, "bat2":
                                   {"imported": 6.33, "exported": 2506.763, "soc": 0}}, "sh":
                               {}, "hc":
                               {"all":
                                   {"imported": 111133.74099238854}}}
EXPECTED_ENTRY_YESTERDAYS_DAILY = {"timestamp": 1698879000, "date": "23:50", "cp":
                                   {"cp5":
                                    {"imported": 0, "exported": 0}, "cp3":
                                       {"imported": 16767.105, "exported": 0}, "cp4":
                                       {"imported": 0, "exported": 0}, "all":
                                       {"imported": 16767.105, "exported": 0}}, "ev":
                                   {"ev0":
                                       {"soc": 0}}, "counter":
                                   {"counter0":
                                       {"imported": 6616.028, "exported": 20.152, "grid": True}}, "pv":
                                   {"all":
                                       {"exported": 10944}, "pv1":
                                       {"exported": 10944}}, "bat":
                                   {"all":
                                       {"imported": 6.33, "exported": 2506.763, "soc": 0}, "bat2":
                                       {"imported": 6.33, "exported": 2506.763, "soc": 0}}, "sh":
                                   {}, "hc":
                                   {"all":
                                       {"imported": 110943.62398798217}}}


@pytest.mark.parametrize(
    "start_charging, create_log_entry, expected_timestamp",
    (pytest.param("05/16/2022, 07:42:52", False, ReferenceTime.START, id="innerhalb der letzten Stunde angesteckt"),
     pytest.param("05/16/2022, 06:40:52", False, ReferenceTime.MIDDLE, id="vor mehr als einer Stunde angesteckt"),
     pytest.param("05/16/2022, 06:40:52", True, ReferenceTime.END,
                  id="vor mehr als einer Stunde angesteckt, Ladevorgang beenden"),
     )
)
def test_get_reference_position(start_charging: str, create_log_entry: bool, expected_timestamp: float):
    # setup
    cp = Chargepoint(0, Mock())
    cp.data.set.log.timestamp_start_charging = start_charging

    # execution
    timestamp = _get_reference_position(cp, create_log_entry)

    # evaluation
    assert timestamp == expected_timestamp


@pytest.mark.parametrize(
    "reference_position, start_charging, expected_timestamp",
    (pytest.param(ReferenceTime.START, "05/16/2022, 07:42:52", 1652679772,
                  id="innerhalb der letzten Stunde angesteckt"),
     pytest.param(ReferenceTime.MIDDLE, "05/16/2022, 06:40:52", 1652679652, id="vor mehr als einer Stunde angesteckt"),
     pytest.param(ReferenceTime.END, "05/16/2022, 06:40:52", 1652680800,
                  id="vor mehr als einer Stunde angesteckt, Ladevorgang beenden"),
     )
)
def test_get_reference_time(reference_position: ReferenceTime, start_charging: str, expected_timestamp: float):
    # setup
    cp = Chargepoint(0, Mock())
    cp.data.set.log.timestamp_start_charging = start_charging

    # execution
    timestamp = get_reference_time(cp, reference_position)

    # evaluation
    assert timestamp == expected_timestamp


@pytest.mark.parametrize(
    "reference_time, expected_entry",
    (
        pytest.param(1698880731, EXPECTED_ENTRY_TODAYS_DAILY, id="Referenz-Eintrag im heutigen Log"),  # 00:18
        pytest.param(1698879171, EXPECTED_ENTRY_YESTERDAYS_DAILY, id="Referenz-Eintrag im gestrigen Log"),  # 23:52
    )
)
def test_get_reference_entry(reference_time, expected_entry, monkeypatch):
    # setup
    with open("packages/control/chargelog/sample_daily_today.json", "r") as json_file:
        entries_todays_daily_log = json.load(json_file)["entries"]
    with open("packages/control/chargelog/sample_daily_yesterday.json", "r") as json_file:
        content_yesterday = json.load(json_file)
    monkeypatch.setattr(chargelog, "_get_yesterdays_daily_log", Mock(return_value=content_yesterday))

    # execution
    entry = _get_reference_entry(entries_todays_daily_log, reference_time)

    # evaluation
    assert entry == expected_entry


@pytest.mark.parametrize("et_active, expected_costs",
                         (
                             pytest.param(True, 1.1649, id="Et aktiv"),
                             pytest.param(False, 2.5953, id="Et inaktiv"),
                         ))
def test_calc(et_active, expected_costs, monkeypatch):
    # setup
    mock_et_get_current_price = Mock(return_value=0.00008)
    monkeypatch.setattr(data.data.optional_data, "et_get_current_price", mock_et_get_current_price)

    # execution
    costs = _calc({'bat': 0.24, 'cp': 0.0, 'grid': 0.6502, 'pv': 0.1098}, 10000, et_active)

    # evaluation
    assert costs == expected_costs


def test_calculate_charge_cost(monkeypatch):
    # integration test
    # setup
    data.data.cp_data["cp3"].data.set.log.timestamp_start_charging = "11/01/2023, 08:12:40"
    data.data.cp_data["cp3"].data.set.log.imported_since_plugged = 1000
    data.data.cp_data["cp3"].data.set.log.imported_since_mode_switch = 1000
    # Mock today() to values in log-file
    datetime_mock = MagicMock(wraps=datetime.datetime)
    # Thu Nov 02 2023 07:00:51
    datetime_mock.today.return_value = datetime.datetime(2023, 11, 2, 7, 0, 52)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)
    with open("packages/control/chargelog/sample_daily_yesterday.json", "r") as json_file:
        content_yesterday = json.load(json_file)
    monkeypatch.setattr(chargelog, "_get_yesterdays_daily_log", Mock(return_value=content_yesterday))
    with open("packages/control/chargelog/sample_daily_today.json", "r") as json_file:
        content_today = json.load(json_file)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", Mock(return_value=content_today))

    # execution
    calculate_charge_cost(data.data.cp_data["cp3"])

    # evaluation
    # charged energy 2.3kWh, 45,45% Grid, 54,55% PV, Grid 0,3ct/kWh, Pv 0,15ct/kWh
    assert data.data.cp_data["cp3"].data.set.log.costs == 0.5023
