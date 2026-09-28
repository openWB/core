
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
    current_entry = json.loads(json.dumps(daily_log["entries"][-1]))
    current_entry["bat"]["all"]["exported"] = 4000
    current_entry["bat"]["bat2"]["exported"] = 4000
    current_entry["counter"]["counter0"]["imported"] = 4500
    current_entry["cp"]["cp4"]["imported"] = 4100
    current_entry["pv"]["all"]["exported"] = 3000
    current_entry["pv"]["pv1"]["exported"] = 3000
    monkeypatch.setattr(chargelog, "create_entry", Mock(return_value=current_entry))

    with patch("builtins.open", mock_open(read_data=json.dumps(daily_log))):
        calc_energy_costs(cp, True)

    assert cp.data.set.log.charged_energy_by_source == {'bat': 699.57, 'cp': 0.0, 'grid': 1300.14, 'pv': 400.29}
    assert round(cp.data.set.log.costs, 5) == 0.025


def test_calc_charge_cost_short_charge_uses_current_entry(mock_data, monkeypatch):
    cp = Chargepoint(4, None)

    # Kurzer Ladevorgang: insgesamt nur 80 Wh geladen.
    # Es wurde vorher noch kein Energieanteil verbucht.
    cp.data.set.log.imported_since_plugged = 80
    cp.data.set.log.imported_since_mode_switch = 80
    cp.data.set.log.timestamp_mode_switch = 1652683260  # 8:41
    cp.data.get.imported = 4080
    cp.data.set.log.charged_energy_by_source = {
        'bat': 0,
        'cp': 0,
        'grid': 0,
        'pv': 0
    }

    daily_log = mock_daily_log(monkeypatch)

    # Letzter gespeicherter Daily-Log ist 8:40:
    #
    # Grid imported = 2500 Wh
    # PV exported   = 2500 Wh
    # CP imported   = 4000 Wh
    #
    # Jetzt erzeugen wir den Live-Snapshot beim Ladeende um 8:42.
    current_entry = json.loads(json.dumps(daily_log["entries"][-1]))

    current_entry["date"] = "8:42"
    current_entry["timestamp"] = 1652683320

    # Zwischen 8:40 und 8:42:
    #
    # +20 Wh Netz
    # +60 Wh PV
    # =80 Wh Verbrauch/Ladung
    #
    # Erwarteter Strommix:
    # Netz = 20 / 80 = 25 %
    # PV   = 60 / 80 = 75 %

    current_entry["counter"]["counter0"]["imported"] = 2520

    current_entry["pv"]["all"]["exported"] = 2560
    current_entry["pv"]["pv1"]["exported"] = 2560

    current_entry["cp"]["all"]["imported"] = 4080
    current_entry["cp"]["cp4"]["imported"] = 4080

    # _get_reference_entries() soll diesen aktuellen Snapshot verwenden.
    monkeypatch.setattr(
        chargelog,
        "create_entry",
        Mock(return_value=current_entry)
    )

    calc_energy_costs(cp, True)

    assert cp.data.set.log.charged_energy_by_source == pytest.approx({
        'bat': 0,
        'cp': 0,
        'grid': 20,
        'pv': 60
    })

    # Kosten:
    # Netz: 20 Wh * 0.0003 €/Wh  = 0.006 €
    # PV:   60 Wh * 0.00015 €/Wh = 0.009 €
    # Gesamt                         0.015 €
    assert cp.data.set.log.costs == pytest.approx(0.015)


def test_calc_charge_cost_reference_end_unique_price(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = 3950
    cp.data.set.log.timestamp_mode_switch = 1652682600  # 8:30
    cp.data.get.imported = 4100
    cp.data.set.log.charged_energy_by_source = {'grid': 1243, 'pv': 386, 'bat': 671, 'cp': 0.0}
    daily_log = mock_daily_log(monkeypatch)
    current_entry = json.loads(json.dumps(daily_log["entries"][-1]))
    current_entry["bat"]["all"]["exported"] = 4000
    current_entry["bat"]["bat2"]["exported"] = 4000
    current_entry["counter"]["counter0"]["imported"] = 4500
    current_entry["cp"]["cp4"]["imported"] = 4100
    current_entry["pv"]["all"]["exported"] = 3000
    current_entry["pv"]["pv1"]["exported"] = 3000
    monkeypatch.setattr(chargelog, "create_entry", Mock(return_value=current_entry))
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


def test_small_positive_charge_is_assigned_to_energy_sources(mock_data, monkeypatch):
    cp = Chargepoint(4, None)
    charged_energy = 80
    cp.data.set.log.imported_since_plugged = cp.data.set.log.imported_since_mode_switch = charged_energy

    # Beispielhafte Verteilung
    processed_entries = {
        "totals": {
            "cp": {
                "cp4": {
                    "energy_imported": 1000,
                    "bat": 250,
                    "cp": 0,
                    "grid": 500,
                    "pv": 250,
                }
            }
        }
    }
    monkeypatch.setattr(chargelog, "_get_reference_position", Mock(return_value=chargelog.ReferenceTime.START))

    charged_energy_by_source = chargelog.calculate_charged_energy_by_source(
        cp, processed_entries, []
    )

    assert charged_energy_by_source == {'bat': 20, 'cp': 0, 'grid': 40, 'pv': 20}

    assert sum(charged_energy_by_source.values()) == cp.data.set.log.imported_since_mode_switch
