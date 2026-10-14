
import json
from unittest.mock import Mock, mock_open, patch

import pytest

from control import data
from control.chargelog import chargelog
from control.chargelog.chargelog import calc_energy_costs
from control.chargepoint.chargepoint import Chargepoint
from control.general import Prices


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
                              'consumer': {},
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
                              'consumer': {},
                              'timestamp': 1652683200,
                              'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}}],
                 "names": {"bat2": "Speicher2", "cp4": "LP 4", "pv1": "PV 1", "ev0": "EV0", "counter0": "Zähler0"}}
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
        'grid': 1242.8, 'pv': 385.8, 'bat': 671.4, 'cp': 0.0}
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

    assert cp.data.set.log.charged_energy_by_source == {'bat': 28.57, 'cp': 0.0, 'grid': 57.14, 'pv': 14.29}
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

    assert cp.data.set.log.charged_energy_by_source == {'bat': 699.57, 'cp': 0.0, 'grid': 1300.14, 'pv': 400.29}
    assert round(cp.data.set.log.costs, 5) == 0.025


def test_calc_charge_cost_reference_end_unique_price(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4100
    cp.data.set.log.charged_energy_by_source = {'grid': 1243, 'pv': 386, 'bat': 671, 'cp': 0.0}
    daily_log = mock_daily_log(monkeypatch)
    data.data.general_data.data.prices = Prices(bat=0.0002, cp=0, grid=0.0002, pv=0.0002)

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp, True)

    assert cp.data.set.log.charged_energy_by_source == {'bat': 699.57, 'cp': 0.0, 'grid': 1300.14, 'pv': 400.29}
    assert round(cp.data.set.log.costs, 5) == 0.79


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
                                        'consumer': {},
                                        'timestamp': 1652682900,
                                        'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}}],
                           "names": {
                               "bat2": "Speicher2", "cp4": "LP 4", "pv1": "PV 1", "ev0": "EV0", "counter0": "Zähler0"}}
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
                              'consumer': {},
                              'timestamp': 1652683200,
                              'prices': {'grid': 0.0003, 'pv': 0.00015, 'bat': 0.0002, 'cp': 0}}],
                 "names": {"bat2": "Speicher2", "cp4": "LP 4", "pv1": "PV 1", "ev0": "EV0", "counter0": "Zähler0"}}
    mock_todays_daily_log = Mock(return_value=daily_log)
    monkeypatch.setattr(chargelog, "get_todays_daily_log", mock_todays_daily_log)

    with patch("builtins.open", side_effect=[
        mock_open(read_data=json.dumps(daily_log)),
        mock_open(read_data=json.dumps(yesterday_daily_log))
    ]):
        calc_energy_costs(cp)

    assert cp.data.set.log.charged_energy_by_source == {
        'grid': 1242.8, 'pv': 385.8, 'bat': 671.4, 'cp': 0.0}
    assert round(cp.data.set.log.costs, 5) == 0.5


def test_calc_charge_cost_tariff_split(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4050
    cp.data.set.log.charged_energy_by_source = {'bat': 100, 'cp': 0, 'grid': 100, 'pv': 100}
    cp.data.set.log.tariff_split = {"NT": {"energy": 1000, "costs": 0.25},
                                    "Standardpreis": {"energy": 100, "costs": 0.03}}
    daily_log = mock_daily_log(monkeypatch)
    daily_log["entries"][-1]["prices"]["tariff_name"] = "NT"

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp)

    # nur der Netzanteil dieses Intervalls (1242.8 - 100 Wh) mit dem Netzpreis dieses Intervalls
    assert round(cp.data.set.log.tariff_split["NT"]["energy"], 2) == 2142.8
    assert round(cp.data.set.log.tariff_split["NT"]["costs"], 5) == round(0.25 + 1142.8 * 0.0003, 5)
    assert cp.data.set.log.tariff_split["Standardpreis"] == {"energy": 100, "costs": 0.03}
    assert round(cp.data.set.log.costs, 5) == 0.5


@pytest.mark.parametrize("tariff_name", [pytest.param(None, id="dynamischer Tarif"),
                                         pytest.param("missing", id="alter Tageslog-Eintrag")])
def test_calc_charge_cost_without_tariff_name(tariff_name, mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4050
    cp.data.set.log.charged_energy_by_source = {'bat': 100, 'cp': 0, 'grid': 100, 'pv': 100}
    daily_log = mock_daily_log(monkeypatch)
    if tariff_name != "missing":
        daily_log["entries"][-1]["prices"]["tariff_name"] = tariff_name

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp)

    assert cp.data.set.log.tariff_split == {}
    assert round(cp.data.set.log.costs, 5) == 0.5


@pytest.mark.parametrize("tariff_split, expected",
                         [pytest.param({}, None, id="ohne Aufteilung kein Schlüssel"),
                          pytest.param({"NT": {"energy": 18400.123, "costs": 4.73456}},
                                       {"NT": {"energy": 18400.12, "costs": 4.73}}, id="mit Aufteilung")])
def test_create_entry_tariff_split(tariff_split, expected, mock_data, monkeypatch):
    monkeypatch.setattr(chargelog, "calc_energy_costs", Mock())
    cp = Chargepoint(4, None)
    cp.data.get.imported = 4050
    cp.data.set.log.imported_at_mode_switch = 100
    cp.data.set.log.timestamp_mode_switch = 1652682600
    cp.data.set.log.costs = 4.9
    cp.data.set.log.tariff_split = tariff_split

    entry = chargelog._create_entry(cp, Mock())

    assert entry["data"]["costs"] == 4.9
    assert entry["data"].get("tariff_split") == expected


def test_reset_log_data_chargemode_switch_resets_tariff_split(mock_data):
    cp = Chargepoint(4, None)
    cp.data.set.log.tariff_split = {"NT": {"energy": 1000, "costs": 0.25}}

    cp.reset_log_data_chargemode_switch()

    assert cp.data.set.log.tariff_split == {}
