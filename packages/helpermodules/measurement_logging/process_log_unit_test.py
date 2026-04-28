from copy import deepcopy
import json
import os
from typing import Dict
from unittest.mock import Mock, mock_open
import pytest

from helpermodules.measurement_logging.process_log import (
    analyse_percentage,
    _calculate_average_power,
    process_entry,
    get_totals,
    _collect_daily_log_data,
    calc_energy_imported_by_source,
    analyse_percentage_totals,
    CalculationType)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    entries = deepcopy(daily_log_sample)
    totals = get_totals(entries)

    # evaluation
    assert totals == daily_log_totals


@pytest.mark.parametrize("name",
                         ["regular",
                          "negative consumption",
                          "cp export"])
def test_analyse_percentage(name: str,
                            daily_log_entry_percentage: Dict,
                            daily_log_entry_percentage_negative_consumption: Dict,
                            daily_log_entry_percentage_cp_discharge: Dict):
    # setup
    if name == "regular":
        data = daily_log_entry_percentage
        expected = deepcopy(data)
        expected.update({"energy_source": {'bat': 0.2398, 'cp': 0.0, 'grid': 0.6504, 'pv': 0.1099}})
    elif name == "negative consumption":
        data = daily_log_entry_percentage_negative_consumption
        expected = deepcopy(data)
        expected.update({"energy_source": {'bat': 0.0, 'cp': 0.0, 'grid': 0.0, 'pv': 0.0}})
    elif name == "cp export":
        data = daily_log_entry_percentage_cp_discharge
        expected = deepcopy(data)
        expected.update({"energy_source": {'bat': 0.2006, 'cp': 0.1459, 'grid': 0.5441, 'pv': 0.1094}})

    # execution
    entry = analyse_percentage(data)

    # evaluation
    assert entry == expected


@pytest.mark.parametrize("test_case, entry_data, expected_energy_source, should_be_unchanged", [
    (
        "zero_consumption",
        {
            "timestamp": 1234567890,
            "bat": {"all": {"energy_imported": 5.0, "energy_exported": 5.0}},
            "cp": {"all": {"energy_exported": 0.0}},
            "pv": {"all": {"energy_exported": 0.0}},
            "counter": {"counter0": {"grid": True, "energy_imported": 5.0, "energy_exported": 5.0}}
        },
        {"grid": 0, "pv": 0, "bat": 0, "cp": 0},
        False
    ),
    (
        "missing_sections",
        {
            "timestamp": 1234567890,
            "counter": {"counter0": {"grid": True, "energy_imported": 10.0, "energy_exported": 2.0}}
        },
        {"grid": 1.0, "pv": 0.0, "bat": 0.0, "cp": 0.0},
        False
    ),
    (
        "no_grid_counter",
        {
            "timestamp": 1234567890,
            "bat": {"all": {"energy_imported": 0.0, "energy_exported": 5.0}},
            "counter": {"counter0": {"grid": False, "energy_imported": 10.0, "energy_exported": 2.0}}
        },
        None,
        True
    )
])
def test_analyse_percentage_edge_cases(test_case, entry_data, expected_energy_source, should_be_unchanged):
    # execution
    result = analyse_percentage(entry_data)

    # evaluation
    if should_be_unchanged:
        # Entry should be unchanged, no energy_source added due to error
        assert result["timestamp"] == entry_data["timestamp"]
        assert "energy_source" not in result or result.get("energy_source") is None
    else:
        # Energy source should be calculated correctly
        assert result["energy_source"] == expected_energy_source


def test_convert_value_to_kW():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1800


def test_calc_energy_imported_by_source():
    # setup
    entry = {
        "timestamp": 1234567890,
        "energy_source": {"grid": 0.6523, "pv": 0.2487, "bat": 0.0789, "cp": 0.0201},
        "hc": {"all": {"energy_imported": 2345.6}},  # Wh
        "cp": {
            "cp1": {"energy_imported": 15723.4},  # Wh
            "cp2": {"energy_imported": 22108.7}   # Wh
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892.3},  # Wh
            "counter1": {"grid": False, "energy_imported": 8956.7}   # Wh
        }
    }

    # execution
    result = calc_energy_imported_by_source(entry)

    # evaluation - realistic Wh values with decimal precision
    assert result["hc"]["all"]["energy_imported_grid"] == 1530.035   # 2345.6 * 0.6523
    assert result["hc"]["all"]["energy_imported_pv"] == 583.351     # 2345.6 * 0.2487
    assert result["hc"]["all"]["energy_imported_bat"] == 185.068    # 2345.6 * 0.0789
    assert result["hc"]["all"]["energy_imported_cp"] == 47.147     # 2345.6 * 0.0201

    assert result["cp"]["cp1"]["energy_imported_grid"] == 10256.374  # 15723.4 * 0.6523
    assert result["cp"]["cp1"]["energy_imported_pv"] == 3910.41     # 15723.4 * 0.2487
    assert result["cp"]["cp1"]["energy_imported_bat"] == 1240.576    # 15723.4 * 0.0789
    assert result["cp"]["cp1"]["energy_imported_cp"] == 316.04     # 15723.4 * 0.0201

    assert result["cp"]["cp2"]["energy_imported_grid"] == 14421.505  # 22108.7 * 0.6523
    assert result["cp"]["cp2"]["energy_imported_pv"] == 5498.434     # 22108.7 * 0.2487
    assert result["cp"]["cp2"]["energy_imported_bat"] == 1744.376    # 22108.7 * 0.0789
    assert result["cp"]["cp2"]["energy_imported_cp"] == 444.385     # 22108.7 * 0.0201

    assert result["counter"]["counter1"]["energy_imported_grid"] == 5842.455   # 8956.7 * 0.6523
    assert result["counter"]["counter1"]["energy_imported_pv"] == 2227.531     # 8956.7 * 0.2487
    assert result["counter"]["counter1"]["energy_imported_bat"] == 706.684    # 8956.7 * 0.0789
    assert result["counter"]["counter1"]["energy_imported_cp"] == 180.03    # 8956.7 * 0.0201
    # counter0 should not have these fields as it's a grid counter
    assert "energy_imported_grid" not in result["counter"]["counter0"]
    assert "energy_imported_pv" not in result["counter"]["counter0"]
    assert "energy_imported_bat" not in result["counter"]["counter0"]
    assert "energy_imported_cp" not in result["counter"]["counter0"]


def test_analyse_percentage_totals():
    # setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'test_data_analyse_percentage_totals.json')
    with open(json_path, 'r') as f:
        entries = json.load(f)

    totals = {
        "hc": {"all": {"energy_imported": 3500}},  # realistic household total in Wh
        "cp": {
            "cp1": {"energy_imported": 18500},    # realistic EV charging total in Wh
            "cp2": {"energy_imported": 29000},     # another EV total in Wh
            "cp3": {"energy_imported": 11433}     # another EV total in Wh
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892},  # grid counter total in Wh
            "counter1": {"grid": False, "energy_imported": 10000},  # sub-meter total in Wh
            "counter2": {"grid": False, "energy_imported": 8735}   # another sub-meter total in Wh
        }
    }

    # execution
    result = analyse_percentage_totals(entries, totals)

    # evaluation
    # Check hc totals (sum of both entries in Wh)
    assert result["hc"]["all"]["energy_imported_grid"] == 7909   # (4820.5 + 3087.9) Wh = 7908.4 Wh
    assert result["hc"]["all"]["energy_imported_pv"] == 2980     # (1734.2 + 1245.6) Wh = 2979.8 Wh
    assert result["hc"]["all"]["energy_imported_bat"] == 912    # (287.8 + 623.7) Wh = 911.5 Wh
    assert result["hc"]["all"]["energy_imported_cp"] == 273     # (95.3 + 178.4) Wh = 273.7 Wh

    # Check cp totals (in Wh)
    assert result["cp"]["cp1"]["energy_imported_grid"] == 22222  # (12345.7 + 9876.2) Wh = 22221.9 Wh
    assert result["cp"]["cp1"]["energy_imported_pv"] == 8354     # (4632.1 + 3721.8) Wh = 8353.9 Wh
    assert result["cp"]["cp1"]["energy_imported_bat"] == 3300    # (1876.4 + 1423.5) Wh = 3299.9 Wh
    assert result["cp"]["cp1"]["energy_imported_cp"] == 802     # (234.6 + 567.1) Wh = 801.7 Wh

    assert result["cp"]["cp2"]["energy_imported_grid"] == 18721  # 18721.3 Wh (only in first entry)
    assert result["cp"]["cp2"]["energy_imported_pv"] == 7124    # 7123.8 Wh
    assert result["cp"]["cp2"]["energy_imported_bat"] == 2955    # 2954.7 Wh
    assert result["cp"]["cp2"]["energy_imported_cp"] == 313     # 312.9 Wh

    # 11432.6 Wh (only in second entry)
    assert result["cp"]["cp3"]["energy_imported_grid"] == 11433
    assert result["cp"]["cp3"]["energy_imported_pv"] == 4824    # 4823.9 Wh
    assert result["cp"]["cp3"]["energy_imported_bat"] == 2135   # 2134.7 Wh
    assert result["cp"]["cp3"]["energy_imported_cp"] == 689    # 689.2 Wh

    # Check counter totals (in Wh, only non-grid counters)
    assert result["counter"]["counter1"]["energy_imported_grid"] == 12158  # (6234.8 + 5923.1) Wh = 12157.9 Wh
    assert result["counter"]["counter1"]["energy_imported_pv"] == 5123     # (2387.5 + 2734.8) Wh = 5122.3 Wh
    assert result["counter"]["counter1"]["energy_imported_bat"] == 2011    # (923.4 + 1087.6) Wh = 2011.0 Wh
    assert result["counter"]["counter1"]["energy_imported_cp"] == 744     # (445.7 + 298.3) Wh = 744.0 Wh

    # 8734.5 Wh (only in second entry)
    assert result["counter"]["counter2"]["energy_imported_grid"] == 8735
    assert result["counter"]["counter2"]["energy_imported_pv"] == 3290     # 3289.7 Wh
    assert result["counter"]["counter2"]["energy_imported_bat"] == 1634    # 1634.2 Wh
    assert result["counter"]["counter2"]["energy_imported_cp"] == 824     # 823.6 Wh


def test_convert(daily_log_entry_processed, daily_log_sample):
    # setup and execution
    entry = process_entry(daily_log_sample[0], daily_log_sample[1], CalculationType.ALL)

    # evaluation
    assert entry == daily_log_entry_processed


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
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.create_entry', mock_create_entry)

    mock_get_previous_entry = Mock(return_value={"timestamp": 1234567800, "data": "previous"})
    monkeypatch.setattr('helpermodules.measurement_logging.process_log.get_previous_entry', mock_get_previous_entry)

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
