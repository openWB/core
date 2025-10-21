
import json
from unittest.mock import Mock, mock_open, patch

import pytest

from control import data
from control.chargelog import chargelog
from control.chargelog.chargelog import calc_energy_costs
from control.chargepoint.chargepoint import Chargepoint


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.optional_data.et_module = None


def mock_daily_log(monkeypatch):
    daily_log = {"entries": [{'bat': {'all': {'exported': 2000, 'imported': 2000, 'soc': 100},
                                      'bat2': {'exported': 2000, 'imported': 2000, 'soc': 100}},
                              'counter': {'counter0': {'exported': 2000,
                                                       'grid': True,
                                                       'imported': 500}},
                              'cp': {'all': {'exported': 0, 'imported': 2000},
                                     'cp4': {'exported': 0, 'imported': 2000}},
                              'date': "8:35",
                              'ev': {'ev0': {'soc': None}},
                              'hc': {'all': {'imported': 0}},
                              'pv': {'all': {'exported': 2000}, 'pv1': {'exported': 2000}},
                              'sh': {},
                              'timestamp': 1652682900,
                              'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}},
                             {'bat': {'all': {'exported': 3000, 'imported': 2000, 'soc': 100},
                                      'bat2': {'exported': 3000, 'imported': 2000, 'soc': 100}},
                              'counter': {'counter0': {'exported': 2000,
                                                       'grid': True,
                                                       'imported': 2500}},
                              'cp': {'all': {'exported': 0, 'imported': 4000},
                                     'cp4': {'exported': 0, 'imported': 4000}},
                              'date': "8:40",
                              'ev': {'ev0': {'soc': None}},
                              'hc': {'all': {'imported': 0}},
                              'pv': {'all': {'exported': 2500}, 'pv1': {'exported': 2500}},
                              'sh': {},
                              'timestamp': 1652683200,
                              'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}}]}
    mock_todays_daily_log = Mock(return_value=daily_log)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", mock_todays_daily_log)
    return daily_log


def test_calc_charge_cost_reference_middle(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4050
    cp.data.set.log.charged_energy_by_source = {'bat': 100, 'cp': 0, 'grid': 100, 'pv': 100}
    daily_log = mock_daily_log(monkeypatch)

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp)

    assert cp.data.set.log.charged_energy_by_source == {
        'grid': 1243, 'pv': 386, 'bat': 671, 'cp': 0.0}
    assert round(cp.data.set.log.costs, 5) == 0.5


def test_calc_charge_cost_reference_start(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 100
    cp.data.set.log.timestamp_mode_switch = 1652683230  # 8:40:30
    cp.data.get.imported = 4100
    cp.data.set.log.charged_energy_by_source = {'bat': 0, 'cp': 0, 'grid': 0, 'pv': 0}
    daily_log = mock_daily_log(monkeypatch)

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp)

    assert cp.data.set.log.charged_energy_by_source == {
        'bat': 28.549999999999997, 'cp': 0.0, 'grid': 57.15, 'pv': 14.299999999999999}
    assert round(cp.data.set.log.costs, 5) == 0.025


def test_calc_charge_cost_reference_end(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4100
    cp.data.set.log.charged_energy_by_source = {'grid': 1243, 'pv': 386, 'bat': 671, 'cp': 0.0}
    daily_log = mock_daily_log(monkeypatch)

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp, True)

    assert cp.data.set.log.charged_energy_by_source == {'bat': 699.55, 'cp': 0.0, 'grid': 1300.15, 'pv': 400.3}
    assert round(cp.data.set.log.costs, 5) == 0.025


def test_calc_charge_cost_reference_middle_day_change(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4050
    cp.data.set.log.charged_energy_by_source = {'bat': 100, 'cp': 0, 'grid': 100, 'pv': 100}
    yesterday_daily_log = {"entries": [{'bat': {'all': {'exported': 2000, 'imported': 2000, 'soc': 100},
                                                'bat2': {'exported': 2000, 'imported': 2000, 'soc': 100}},
                                        'counter': {'counter0': {'exported': 2000,
                                                                 'grid': True,
                                                                 'imported': 500}},
                                        'cp': {'all': {'exported': 0, 'imported': 2000},
                                               'cp4': {'exported': 0, 'imported': 2000}},
                                        'date': "8:35",
                                        'ev': {'ev0': {'soc': None}},
                                        'hc': {'all': {'imported': 0}},
                                        'pv': {'all': {'exported': 2000}, 'pv1': {'exported': 2000}},
                                        'sh': {},
                                        'timestamp': 1652682900,
                                        'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}}]}
    mock_yesterdays_daily_log = Mock(return_value=yesterday_daily_log)
    monkeypatch.setattr(chargelog, "get_daily_log", mock_yesterdays_daily_log)

    daily_log = {"entries": [{'bat': {'all': {'exported': 3000, 'imported': 2000, 'soc': 100},
                                      'bat2': {'exported': 3000, 'imported': 2000, 'soc': 100}},
                              'counter': {'counter0': {'exported': 2000,
                                                       'grid': True,
                                                       'imported': 2500}},
                              'cp': {'all': {'exported': 0, 'imported': 4000},
                                     'cp4': {'exported': 0, 'imported': 4000}},
                              'date': "8:40",
                              'ev': {'ev0': {'soc': None}},
                              'hc': {'all': {'imported': 0}},
                              'pv': {'all': {'exported': 2500}, 'pv1': {'exported': 2500}},
                              'sh': {},
                              'timestamp': 1652683200,
                              'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}}]}
    mock_todays_daily_log = Mock(return_value=daily_log)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", mock_todays_daily_log)

    with patch("builtins.open", side_effect=[
        mock_open(read_data=json.dumps(daily_log)),
        mock_open(read_data=json.dumps(yesterday_daily_log))
    ]):
        calc_energy_costs(cp)

    assert cp.data.set.log.charged_energy_by_source == {
        'grid': 1243, 'pv': 386, 'bat': 671, 'cp': 0.0}
    assert round(cp.data.set.log.costs, 5) == 0.5