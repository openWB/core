import json
from unittest.mock import Mock

import pytest
from control import data
from control.chargelog import chargelog
from control.chargelog.chargelog import (ReferenceTime, _calc, _get_reference_entry, _get_reference_position,
                                         calculate_charge_cost, get_reference_time)
from control.chargepoint.chargepoint import Chargepoint
from control.general import General
from control.optional import Optional
from helpermodules import timecheck


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
    (pytest.param(1652679772, False, ReferenceTime.START,
                  id="innerhalb der letzten Stunde angesteckt"),  # "05/16/2022, 07:42:52"
     pytest.param(1652676052, False, ReferenceTime.MIDDLE,
                  id="vor mehr als einer Stunde angesteckt"),  # "05/16/2022, 06:40:52"
     pytest.param(1652676052, True, ReferenceTime.END,
                  id="vor mehr als einer Stunde angesteckt, Ladevorgang beenden"),  # "05/16/2022, 06:40:52"
     )
)
def test_get_reference_position(start_charging: str, create_log_entry: bool, expected_timestamp: float):
    # setup
    # jetzt ist "05/16/2022, 08:40:52"
    cp = Chargepoint(0, Mock())
    cp.data.set.log.timestamp_start_charging = start_charging

    # execution
    timestamp = _get_reference_position(cp, create_log_entry)

    # evaluation
    assert timestamp == expected_timestamp


@pytest.mark.parametrize(
    "reference_position, start_charging, expected_timestamp",
    (pytest.param(ReferenceTime.START, 1652679772, 1652679772,
                  id="innerhalb der letzten Stunde begonnen"),  # "05/16/2022, 07:42:52"
     pytest.param(ReferenceTime.MIDDLE, 1652676052, 1652679712,
                  id="vor Stundenwechsel begonnen"),  # "05/16/2022, 06:40:52"
     pytest.param(ReferenceTime.END, 1652676052, 1652680860,
                  id="vor Stundenwechsel begonnen, Ladevorgang beenden"),  # "05/16/2022, 06:40:52"
     )
)
def test_get_reference_time(reference_position: ReferenceTime, start_charging: str, expected_timestamp: float):
    # setup
    # jetzt ist "05/16/2022, 08:40:52"
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
def test_calc(et_active: bool, expected_costs: float, monkeypatch: pytest.MonkeyPatch):
    # setup
    mock_et_get_current_price = Mock(return_value=0.00008)
    monkeypatch.setattr(data.data.optional_data, "et_get_current_price", mock_et_get_current_price)

    # execution
    costs = _calc({'bat': 0.24, 'cp': 0.0, 'grid': 0.6502, 'pv': 0.1098}, 10000, et_active)

    # evaluation
    assert costs == expected_costs


CREATE_LOG = {'bat': {'all': {'exported': 2506.763, 'imported': 6.33, 'soc': 0},
                      'bat2': {'exported': 2506.763, 'imported': 6.33, 'soc': 0}},
              'counter': {'counter0': {'exported': 20.152,
                                       'grid': True,
                                       'imported': 15584.117}},
              'cp': {'all': {'exported': 0, 'imported': 33245.051},
                     'cp3': {'exported': 0, 'imported': 33245.051},
                     'cp4': {'exported': 0, 'imported': 0},
                     'cp5': {'exported': 0, 'imported': 0}},
              'date': '07:00:51',
              'ev': {'ev0': {'soc': 0}},
              'hc': {'all': {'imported': 114169.25077207937}},
              'pv': {'all': {'exported': 21692}, 'pv1': {'exported': 21692}},
              'sh': {},
              'timestamp': 1698904851}


def test_calculate_charge_cost(monkeypatch: pytest.MonkeyPatch):
    # integration test
    # setup
    data.data.cp_data["cp3"].data.set.log.timestamp_start_charging = 1698822760  # Wed Nov 01 2023 08:12:40
    data.data.cp_data["cp3"].data.set.log.imported_since_plugged = 1000
    data.data.cp_data["cp3"].data.set.log.imported_since_mode_switch = 1000
    data.data.cp_data["cp3"].data.get.imported = 33245.051
    # Mock today() to values in log-file
    # Thu Nov 02 2023 07:00:51
    mock_today_timestamp = Mock(return_value=1698904851)
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)
    with open("packages/control/chargelog/sample_daily_yesterday.json", "r") as json_file:
        content_yesterday = json.load(json_file)
    monkeypatch.setattr(chargelog, "_get_yesterdays_daily_log", Mock(return_value=content_yesterday))
    with open("packages/control/chargelog/sample_daily_today.json", "r") as json_file:
        content_today = json.load(json_file)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", Mock(return_value=content_today))
    create_entry_mock = Mock(return_value=CREATE_LOG)
    monkeypatch.setattr(chargelog, "create_entry", create_entry_mock)

    # execution
    calculate_charge_cost(data.data.cp_data["cp3"])

    # evaluation
    # charged energy 2.3kWh, 45,45% Grid, 54,55% PV, Grid 0,3ct/kWh, Pv 0,15ct/kWh
    assert data.data.cp_data["cp3"].data.set.log.costs == 0.5023


CREATE_LOG_1 = {'bat': {'all': {'exported': 2506.763, 'imported': 6.33, 'soc': 0},
                        'bat2': {'exported': 2506.763, 'imported': 6.33, 'soc': 0}},
                'counter': {'counter0': {'exported': 20.152,
                                         'grid': True,
                                         'imported': 14327.787}},
                'cp': {'all': {'exported': 0, 'imported': 30942.764},
                       'cp3': {'exported': 0, 'imported': 30942.764},
                       'cp4': {'exported': 0, 'imported': 0},
                       'cp5': {'exported': 0, 'imported': 0}},
                'date': '06:00',
                'ev': {'ev0': {'soc': 0}},
                'hc': {'all': {'imported': 113712.84747947555}},
                'pv': {'all': {'exported': 20185}, 'pv1': {'exported': 20185}},
                'sh': {},
                'timestamp': 1698901200}

CREATE_LOG_2 = {'bat': {'all': {'exported': 2506.763, 'imported': 6.33, 'soc': 0},
                        'bat2': {'exported': 2506.763, 'imported': 6.33, 'soc': 0}},
                'counter': {'counter0': {'exported': 20.152,
                                         'grid': True,
                                         'imported': 15584.117}},
                'cp': {'all': {'exported': 0, 'imported': 33245.051},
                       'cp3': {'exported': 0, 'imported': 33245.051},
                       'cp4': {'exported': 0, 'imported': 0},
                       'cp5': {'exported': 0, 'imported': 0}},
                'date': '07:00',
                'ev': {'ev0': {'soc': 0}},
                'hc': {'all': {'imported': 114169.25077207937}},
                'pv': {'all': {'exported': 21692}, 'pv1': {'exported': 21692}},
                'sh': {},
                'timestamp': 1698904800}

CREATE_LOG_3 = {'bat': {'all': {'exported': 2506.763, 'imported': 6.33, 'soc': 0},
                        'bat2': {'exported': 2506.763, 'imported': 6.33, 'soc': 0}},
                'counter': {'counter0': {'exported': 20.152,
                                         'grid': True,
                                         'imported': 15839.117}},
                'cp': {'all': {'exported': 0, 'imported': 33500},
                       'cp3': {'exported': 0, 'imported': 33500},
                       'cp4': {'exported': 0, 'imported': 0},
                       'cp5': {'exported': 0, 'imported': 0}},
                'date': '07:02',
                'ev': {'ev0': {'soc': 0}},
                'hc': {'all': {'imported': 114169.25077207937}},
                'pv': {'all': {'exported': 21692}, 'pv1': {'exported': 21692}},
                'sh': {},
                'timestamp': 1698904800}


def test_calculate_charge_cost_full_hour(monkeypatch: pytest.MonkeyPatch):
    # integration test charging 1.5 h
    # setup
    data.data.cp_data["cp3"].data.set.log.timestamp_start_charging = 1698900420  # Thu Nov 02 2023 05:47:00
    data.data.cp_data["cp3"].data.set.log.imported_since_plugged = 1000
    data.data.cp_data["cp3"].data.set.log.imported_since_mode_switch = 1000
    # simplify cost structure
    data.data.general_data.data.prices.bat = 0.0003
    data.data.general_data.data.prices.grid = 0.0003
    data.data.general_data.data.prices.pv = 0.0003
    with open("packages/control/chargelog/sample_daily_yesterday.json", "r") as json_file:
        content_yesterday = json.load(json_file)
    monkeypatch.setattr(chargelog, "_get_yesterdays_daily_log", Mock(return_value=content_yesterday))
    with open("packages/control/chargelog/sample_daily_today.json", "r") as json_file:
        content_today = json.load(json_file)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", Mock(return_value=content_today))
    create_entry_mock = Mock(side_effect=[CREATE_LOG_1, CREATE_LOG_2, CREATE_LOG_3])
    monkeypatch.setattr(chargelog, "create_entry", create_entry_mock)

    # execution
    # Berechnung nach der ersten Viertel-Stunde ReferenceTime.START
    # Mock today() to values in log-file
    mock_today_timestamp = Mock(return_value=1698901200)  # 6:00
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)
    calculate_charge_cost(data.data.cp_data["cp3"])

    # Berechnung nach den ersten 1.25h ReferenceTime.MIDDLE
    mock_today_timestamp = Mock(return_value=1698904800)  # 07:00
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)
    calculate_charge_cost(data.data.cp_data["cp3"])

    # Berechnung nach 1.5 h (Ladeende) ReferenceTime.END
    data.data.cp_data["cp3"].data.set.log.imported_since_plugged = 3557.236
    data.data.cp_data["cp3"].data.set.log.imported_since_mode_switch = 3557.236
    data.data.cp_data["cp3"].data.get.imported = 33500
    mock_today_timestamp = Mock(return_value=1698904920)  # 7:02
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)
    calculate_charge_cost(data.data.cp_data["cp3"], create_log_entry=True)

    # evaluation
    # 3557.236Wh * 0,3€/kWh = 1.06€
    # 5:45-6:00 1000Wh; 0,3€
    # 6:00-7:00 33245.051-30942.764 = 2302.287Wh; 0,69€
    # 7:00-7:02 254.949 Wh; 0,08€
    assert data.data.cp_data["cp3"].data.set.log.costs == 1.0672
