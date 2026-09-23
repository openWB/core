from copy import deepcopy
import json
import os
from unittest.mock import Mock, mock_open
import pytest

from helpermodules.measurement_logging.process_log import (
    get_totals,
    _collect_daily_log_data,
    _get_last_entry_for_period,
    _apply_source_totals,
    analyse_percentage_totals)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    entries = deepcopy(daily_log_sample)
    totals = get_totals(entries)

    # evaluation
    assert totals == daily_log_totals


def test_analyse_percentage_totals():
    # setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'test_data_analyse_percentage_totals.json')
    with open(json_path, 'r') as f:
        entries = json.load(f)

    totals = {
        "hc": {"all": {"energy_imported": 3500}},
        "cp": {
            "all": {"energy_imported": 58933},
            "cp1": {"energy_imported": 18500},
            "cp2": {"energy_imported": 29000},
            "cp3": {"energy_imported": 11433}
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892},
            "counter1": {"grid": False, "energy_imported": 10000},
            "counter2": {"grid": False, "energy_imported": 8735}
        },
        "consumer": {
            "all": {"energy_imported": 10928},
            "consumer6": {"energy_imported": 4248},
            "consumer7": {"energy_imported": 7182}
        }
    }

    # execution
    result = analyse_percentage_totals(entries, totals)

    # evaluation
    # Check hc totals (sum of both entries in Wh)
    assert result["hc"]["all"]["energy_imported_grid"] == 7909
    assert result["hc"]["all"]["energy_imported_pv"] == 2980
    assert result["hc"]["all"]["energy_imported_bat"] == 912
    assert result["hc"]["all"]["energy_imported_cp"] == 273

    assert result["cp"]["all"]["energy_imported_grid"] == 52376
    assert result["cp"]["all"]["energy_imported_pv"] == 20302
    assert result["cp"]["all"]["energy_imported_bat"] == 8390
    assert result["cp"]["all"]["energy_imported_cp"] == 1804

    # Check cp totals (in Wh)
    assert result["cp"]["cp1"]["energy_imported_grid"] == 22222
    assert result["cp"]["cp1"]["energy_imported_pv"] == 8354
    assert result["cp"]["cp1"]["energy_imported_bat"] == 3300
    assert result["cp"]["cp1"]["energy_imported_cp"] == 802

    assert result["cp"]["cp2"]["energy_imported_grid"] == 18721
    assert result["cp"]["cp2"]["energy_imported_pv"] == 7124
    assert result["cp"]["cp2"]["energy_imported_bat"] == 2955
    assert result["cp"]["cp2"]["energy_imported_cp"] == 313

    # 11432.6 Wh (only in second entry)
    assert result["cp"]["cp3"]["energy_imported_grid"] == 11433
    assert result["cp"]["cp3"]["energy_imported_pv"] == 4824
    assert result["cp"]["cp3"]["energy_imported_bat"] == 2135
    assert result["cp"]["cp3"]["energy_imported_cp"] == 689

    # Check counter totals (in Wh, only non-grid counters)
    assert result["counter"]["counter1"]["energy_imported_grid"] == 12158
    assert result["counter"]["counter1"]["energy_imported_pv"] == 5123
    assert result["counter"]["counter1"]["energy_imported_bat"] == 2011
    assert result["counter"]["counter1"]["energy_imported_cp"] == 744

    # 8734.5 Wh (only in second entry)
    assert result["counter"]["counter2"]["energy_imported_grid"] == 8735
    assert result["counter"]["counter2"]["energy_imported_pv"] == 3290
    assert result["counter"]["counter2"]["energy_imported_bat"] == 1634
    assert result["counter"]["counter2"]["energy_imported_cp"] == 824

    assert result["consumer"]["all"]["energy_imported_grid"] == 6858
    assert result["consumer"]["all"]["energy_imported_pv"] == 2468
    assert result["consumer"]["all"]["energy_imported_bat"] == 1134
    assert result["consumer"]["all"]["energy_imported_cp"] == 468

    assert result["consumer"]["consumer6"]["energy_imported_grid"] == 2468
    assert result["consumer"]["consumer6"]["energy_imported_pv"] == 1134
    assert result["consumer"]["consumer6"]["energy_imported_bat"] == 468
    assert result["consumer"]["consumer6"]["energy_imported_cp"] == 178

    assert result["consumer"]["consumer7"]["energy_imported_grid"] == 4890
    assert result["consumer"]["consumer7"]["energy_imported_pv"] == 1356
    assert result["consumer"]["consumer7"]["energy_imported_bat"] == 690
    assert result["consumer"]["consumer7"]["energy_imported_cp"] == 246


def test_analyse_percentage_totals_entry_missing_grid_counter():
    # Ein Eintrag, bei dem analyse_percentage() zuvor fehlgeschlagen ist (z.B. weil der EVU-Zähler
    # nicht als "grid" markiert wurde), hat kein "energy_source" und calc_energy_imported_by_source()
    # setzt für dessen Zähler dann kein "energy_imported_*". Das darf die Auswertung der übrigen,
    # intakten Einträge nicht mit einem KeyError abbrechen.
    entries = [
        {
            "hc": {},
            "cp": {},
            "consumer": {},
            "counter": {
                "counter0": {"grid": False},  # fehlerhafter Eintrag ohne "energy_imported_*"
            },
        },
        {
            "hc": {},
            "cp": {},
            "consumer": {},
            "counter": {
                "counter0": {"grid": False, "energy_imported_grid": 100, "energy_imported_pv": 50,
                             "energy_imported_bat": 20, "energy_imported_cp": 10},
            },
        },
    ]
    totals = {
        "hc": {},
        "cp": {},
        "consumer": {},
        "counter": {"counter0": {"grid": False, "energy_imported": 100}},
    }

    result = analyse_percentage_totals(entries, totals)

    assert result["counter"]["counter0"]["energy_imported_grid"] == 100
    assert result["counter"]["counter0"]["energy_imported_pv"] == 50
    assert result["counter"]["counter0"]["energy_imported_bat"] == 20
    assert result["counter"]["counter0"]["energy_imported_cp"] == 10


def test_collect_daily_log_data_current_day(monkeypatch):
    # setup
    test_date = "20240422"
    mock_log_data = {
        "entries": [{"timestamp": 1234567890, "data": "test"}],
        "names": {}
    }
    mock_current_entry = {"timestamp": 1234567999, "data": "current"}

    mock_timecheck = Mock()
    mock_timecheck.create_timestamp_YYYYMMDD.return_value = test_date
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.timecheck', mock_timecheck)

    mock_json_load = Mock(return_value=mock_log_data)
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.json.load', mock_json_load)

    mock_create_entry = Mock(return_value=mock_current_entry)
    monkeypatch.setattr('helpermodules.measurement_logging.write_log.create_entry', mock_create_entry)

    mock_get_previous_entry = Mock(return_value={"timestamp": 1234567800, "data": "previous"})
    monkeypatch.setattr('helpermodules.measurement_logging.write_log.get_previous_entry', mock_get_previous_entry)

    monkeypatch.setattr('builtins.open', mock_open(read_data=json.dumps(mock_log_data)))

    # execution
    result = _collect_daily_log_data(test_date)

    # evaluation
    expected_result = {
        "entries": [
            {"timestamp": 1234567890, "data": "test"},
            {"timestamp": 1234567999, "data": "current"}
        ],
        "names": {}
    }
    assert result == expected_result


def test_collect_daily_log_data_past_date_with_next_day(monkeypatch):
    # setup
    test_date = "20240422"
    next_date = "20240423"
    mock_current_log_data = {
        "entries": [{"timestamp": 1234567890, "data": "test"}],
        "names": {}
    }
    mock_next_log_data = {
        "entries": [{"timestamp": 1234567999, "data": "next_day"}]
    }

    mock_timecheck = Mock()
    mock_timecheck.create_timestamp_YYYYMMDD.return_value = "20240425"
    mock_timecheck.get_relative_date_string.return_value = next_date
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.timecheck', mock_timecheck)

    mock_json_load = Mock(side_effect=[mock_current_log_data, mock_next_log_data])
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.json.load', mock_json_load)

    monkeypatch.setattr('builtins.open', mock_open())

    # execution
    result = _collect_daily_log_data(test_date)

    # evaluation
    expected_result = {
        "entries": [
            {"timestamp": 1234567890, "data": "test"},
            {"timestamp": 1234567999, "data": "next_day"}
        ],
        "names": {}
    }
    assert result == expected_result


def test_collect_daily_log_data_file_not_found(monkeypatch):
    # setup
    test_date = "20240422"

    mock_timecheck = Mock()
    mock_timecheck.create_timestamp_YYYYMMDD.return_value = "20240425"
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.timecheck', mock_timecheck)

    def mock_open_side_effect(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr('builtins.open', mock_open_side_effect)

    # execution
    result = _collect_daily_log_data(test_date)

    # evaluation
    expected_result = {"entries": [], "names": {}}
    assert result == expected_result


def test_collect_daily_log_data_json_decode_error(monkeypatch):
    # setup
    test_date = "20240422"

    mock_timecheck = Mock()
    mock_timecheck.create_timestamp_YYYYMMDD.return_value = "20240425"
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.timecheck', mock_timecheck)

    mock_json_load = Mock(side_effect=json.JSONDecodeError("msg", "doc", 1))
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.json.load', mock_json_load)

    monkeypatch.setattr('builtins.open', mock_open(read_data="invalid json"))

    # execution
    result = _collect_daily_log_data(test_date)

    # evaluation
    expected_result = {"entries": [], "names": {}}
    assert result == expected_result


def test_apply_source_totals_updates_existing_and_creates_missing_sections():
    # setup
    entry = {
        "cp": {
            "all": {"energy_imported": 5, "keep": "x"},
            "cp9": {"keep_cp": True}
        },
        "meta": {"unchanged": True}
    }
    daily_totals = {
        "cp": {
            "all": {"energy_imported": 12, "energy_exported": 3},
            "cp1": {"energy_imported": 7},
            "cp_invalid": 99
        },
        "hc": {
            "all": {"energy_imported": 2}
        },
        "invalid_section": "ignore_me"
    }

    # execution
    result = _apply_source_totals(entry, daily_totals)

    # evaluation
    # in-place behavior
    assert result is entry

    # existing module gets overwritten/extended, unrelated fields stay
    assert result["cp"]["all"]["energy_imported"] == 12
    assert result["cp"]["all"]["energy_exported"] == 3
    assert result["cp"]["all"]["keep"] == "x"

    # missing module and section are created
    assert result["cp"]["cp1"]["energy_imported"] == 7
    assert result["hc"]["all"]["energy_imported"] == 2

    # invalid totals are ignored
    assert "cp_invalid" not in result["cp"]
    assert "invalid_section" not in result

    # unrelated data stays unchanged
    assert result["cp"]["cp9"]["keep_cp"] is True
    assert result["meta"]["unchanged"] is True


@pytest.mark.parametrize(
    "entries, period, period_format, expected",
    [
        (
            [
                {"timestamp": 1711929600, "value": "april_1"},
                {"timestamp": 1712016000, "value": "april_2"},
                {"timestamp": 1714608000, "value": "may_2"},
            ],
            "202404",
            "%Y%m",
            {"timestamp": 1712016000, "value": "april_2"},
        ),
        (
            [],
            "202404",
            "%Y%m",
            None,
        ),
    ],
)
def test_get_last_entry_for_period(entries, period, period_format, expected):
    # execution
    result = _get_last_entry_for_period(entries, period, period_format)

    # evaluation
    assert result == expected
