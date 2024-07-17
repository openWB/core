
import datetime
from unittest.mock import Mock

import pytest

from control import data
from control.chargelog import chargelog
from control.chargelog.chargelog import calculate_charge_cost
from control.chargepoint.chargepoint import Chargepoint
from helpermodules import timecheck
from test_utils.test_environment import running_on_github


def mock_daily_log_with_charging(date: str, num_of_intervalls, monkeypatch):
    """erzeugt ein daily_log, im ersten Eintrag gibt es keine Änderung, danach wird bis inklusive dem letzten Beitrag
    geladen"""
    bat_exported = pv_exported = cp_imported = counter_imported = 2000
    date = datetime.datetime.strptime(date, "%m/%d/%Y, %H:%M")
    daily_log = {"entries": []}
    for i in range(0, num_of_intervalls):
        if i != 0:
            bat_exported += 1000
            pv_exported += 500
            cp_imported += 2000
            counter_imported += 500
        daily_log["entries"].append({'bat': {'all': {'exported': bat_exported, 'imported': 2000, 'soc': 100},
                                             'bat2': {'exported': bat_exported, 'imported': 2000, 'soc': 100}},
                                     'counter': {'counter0': {'exported': 2000,
                                                              'grid': True,
                                                              'imported': counter_imported}},
                                     'cp': {'all': {'exported': 0, 'imported': cp_imported},
                                            'cp4': {'exported': 0, 'imported': cp_imported}},
                                     'date': date.strftime("%H:%M"),
                                     'ev': {'ev0': {'soc': None}},
                                     'hc': {'all': {'imported': 0}},
                                     'pv': {'all': {'exported': pv_exported}, 'pv1': {'exported': pv_exported}},
                                     'sh': {},
                                     'timestamp': date.timestamp()})
        date += datetime.timedelta(minutes=5)
    mock_todays_daily_log = Mock(return_value=daily_log)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", mock_todays_daily_log)
    return daily_log


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data.et_module = None


def mock_create_entry_reference_end(clock, daily_log, monkeypatch):
    current_log = daily_log["entries"][-1]
    current_log["cp"]["all"]["imported"] += 500
    current_log["cp"]["cp4"]["imported"] += 500
    current_log["counter"]["counter0"]["imported"] += 500
    current_log["date"] = clock
    current_log["timestamp"] = datetime.datetime.strptime(f"05/16/2022, {clock}", "%m/%d/%Y, %H:%M").timestamp()
    mock_create_entry = Mock(return_value=current_log)
    monkeypatch.setattr(chargelog, "create_entry", mock_create_entry)


def init_cp(charged_energy, costs, start_hour, start_minute=47):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = charged_energy
    cp.data.set.log.timestamp_start_charging = datetime.datetime(2022, 5, 16, start_hour, start_minute).timestamp()
    cp.data.get.imported = charged_energy + 2000
    cp.data.set.log.costs = costs
    return cp


def test_calc_charge_cost_no_hour_change_reference_end(mock_data, monkeypatch):
    cp = init_cp(6500, 0, 10, start_minute=27)
    daily_log = mock_daily_log_with_charging("05/16/2022, 10:25", 4, monkeypatch)
    mock_create_entry_reference_end("10:42", daily_log, monkeypatch)

    calculate_charge_cost(cp, True)

    assert cp.data.set.log.costs == 1.425


def test_calc_charge_cost_first_hour_change_reference_begin(mock_data, monkeypatch):
    cp = init_cp(6000, 0, 7)
    daily_log = mock_daily_log_with_charging("05/16/2022, 07:45", 4, monkeypatch)
    current_log = daily_log["entries"][-1]
    current_log["date"] = "08:00"
    current_log["timestamp"] = datetime.datetime.strptime("05/16/2022, 08:00", "%m/%d/%Y, %H:%M").timestamp()
    mock_create_entry = Mock(return_value=current_log)
    monkeypatch.setattr(chargelog, "create_entry", mock_create_entry)

    calculate_charge_cost(cp, False)

    assert cp.data.set.log.costs == 1.275


def test_calc_charge_cost_first_hour_change_reference_begin_day_change(mock_data, monkeypatch):
    cp = init_cp(6000, 0, 23)
    daily_log = mock_daily_log_with_charging("05/16/2022, 23:45", 4, monkeypatch)
    current_log = daily_log["entries"][-1]
    current_log["date"] = "00:00"
    current_log["timestamp"] = datetime.datetime.strptime("05/17/2022, 00:00", "%m/%d/%Y, %H:%M").timestamp()
    mock_create_entry = Mock(return_value=current_log)
    monkeypatch.setattr(chargelog, "create_entry", mock_create_entry)
    mock_today_timestamp = Mock(return_value=1652738421)
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)

    calculate_charge_cost(cp, False)

    assert cp.data.set.log.costs == 1.275


def test_calc_charge_cost_one_hour_change_reference_end(mock_data, monkeypatch):
    if running_on_github():
        # ToDo Zeitzonen berücksichtigen, damit Tests auf Github laufen
        return
    cp = init_cp(22500, 1.275, 7)
    daily_log = mock_daily_log_with_charging("05/16/2022, 07:45", 12, monkeypatch)
    mock_create_entry_reference_end("08:40", daily_log, monkeypatch)

    calculate_charge_cost(cp, True)

    assert cp.data.set.log.costs == 4.8248999999999995


def test_calc_charge_cost_two_hour_change_reference_middle(mock_data, monkeypatch):
    if running_on_github():
        # ToDo Zeitzonen berücksichtigen, damit Tests auf Github laufen
        return
    cp = init_cp(22500, 1.275, 6)
    daily_log = mock_daily_log_with_charging("05/16/2022, 06:45", 16, monkeypatch)
    current_log = daily_log["entries"][-1]
    current_log["date"] = "08:00"
    current_log["timestamp"] = datetime.datetime(2022, 5, 16, 8).timestamp()
    mock_create_entry = Mock(return_value=current_log)
    monkeypatch.setattr(chargelog, "create_entry", mock_create_entry)
    mock_today_timestamp = Mock(return_value=1652680801)
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)

    calculate_charge_cost(cp, False)

    assert cp.data.set.log.costs == 6.375


def test_calc_charge_cost_two_hour_change_reference_end(mock_data, monkeypatch):
    if running_on_github():
        # ToDo Zeitzonen berücksichtigen, damit Tests auf Github laufen
        return
    cp = init_cp(46500, 6.375, 6)
    daily_log = mock_daily_log_with_charging("05/16/2022, 06:45", 24, monkeypatch)
    mock_create_entry_reference_end("08:40", daily_log, monkeypatch)

    calculate_charge_cost(cp, True)

    assert cp.data.set.log.costs == 9.924900000000001
