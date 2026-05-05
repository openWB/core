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
    entry, message = analyse_percentage(data)

    # evaluation
    assert entry == expected
    assert message == ""


@pytest.mark.parametrize("test_case, entry_data, expected_energy_source, should_be_unchanged", [
    (
        "zero_consumption",
        {
            "timestamp": 1234567890,
            "date": "00:31",
            "bat": {"all": {"energy_imported": 5.0, "energy_exported": 5.0, "fault_state": 0}},
            "cp": {"all": {"energy_exported": 0.0, "fault_state": 0}},
            "pv": {"all": {"energy_exported": 0.0, "fault_state": 0}},
            "counter": {"counter0": {"grid": True, "energy_imported": 5.0, "energy_exported": 5.0, "fault_state": 0}}
        },
        {"grid": 0, "pv": 0, "bat": 0, "cp": 0},
        False
    ),
    (
        "missing_sections",
        {
            "timestamp": 1234567890,
            "date": "00:31",
            "counter": {"counter0": {"grid": True, "energy_imported": 10.0, "energy_exported": 2.0, "fault_state": 0}}
        },
        {"grid": 1.0, "pv": 0.0, "bat": 0.0, "cp": 0.0},
        False
    ),
    (
        "no_grid_counter",
        {
            "timestamp": 1234567890,
            "date": "00:31",
            "bat": {"all": {"energy_imported": 0.0, "energy_exported": 5.0, "fault_state": 0}},
            "counter": {"counter0": {"grid": False, "energy_imported": 10.0, "energy_exported": 2.0, "fault_state": 0}}
        },
        None,
        True
    )
])
def test_analyse_percentage_edge_cases(test_case, entry_data, expected_energy_source, should_be_unchanged):
    # execution
    result, message = analyse_percentage(entry_data)

    # evaluation
    if should_be_unchanged:
        # Entry should be unchanged, no energy_source added due to error
        assert result["timestamp"] == entry_data["timestamp"]
        assert "energy_source" not in result or result.get("energy_source") is None
    else:
        # Energy source should be calculated correctly
        assert result["energy_source"] == expected_energy_source
        assert message == ""


def test_calculate_average_power():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1800


def test_calc_energy_imported_by_source():
    # setup
    entry = {
        "timestamp": 1234567890,
        "energy_source": {"grid": 0.6523, "pv": 0.2487, "bat": 0.0789, "cp": 0.0201},
        "hc": {"all": {"energy_imported": 2345.6, "fault_state": 0}},
        "cp": {
            "cp1": {"energy_imported": 15723.4, "fault_state": 0},
            "cp2": {"energy_imported": 22108.7, "fault_state": 0}
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892.3, "fault_state": 0},
            "counter1": {"grid": False, "energy_imported": 8956.7, "fault_state": 0}
        }
    }

    # execution
    result, message = calc_energy_imported_by_source(entry, {})

    # evaluation - realistic Wh values with decimal precision
    assert result["hc"]["all"]["energy_imported_grid"] == 1530.035
    assert result["hc"]["all"]["energy_imported_pv"] == 583.351
    assert result["hc"]["all"]["energy_imported_bat"] == 185.068
    assert result["hc"]["all"]["energy_imported_cp"] == 47.147

    assert result["cp"]["cp1"]["energy_imported_grid"] == 10256.374
    assert result["cp"]["cp1"]["energy_imported_pv"] == 3910.41
    assert result["cp"]["cp1"]["energy_imported_bat"] == 1240.576
    assert result["cp"]["cp1"]["energy_imported_cp"] == 316.04

    assert result["cp"]["cp2"]["energy_imported_grid"] == 14421.505
    assert result["cp"]["cp2"]["energy_imported_pv"] == 5498.434
    assert result["cp"]["cp2"]["energy_imported_bat"] == 1744.376
    assert result["cp"]["cp2"]["energy_imported_cp"] == 444.385

    assert result["counter"]["counter1"]["energy_imported_grid"] == 5842.455
    assert result["counter"]["counter1"]["energy_imported_pv"] == 2227.531
    assert result["counter"]["counter1"]["energy_imported_bat"] == 706.684
    assert result["counter"]["counter1"]["energy_imported_cp"] == 180.03
    # counter0 should not have these fields as it's a grid counter
    assert "energy_imported_grid" not in result["counter"]["counter0"]
    assert "energy_imported_pv" not in result["counter"]["counter0"]
    assert "energy_imported_bat" not in result["counter"]["counter0"]
    assert "energy_imported_cp" not in result["counter"]["counter0"]
    assert message == ""


def test_analyse_percentage_totals():
    # setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'test_data_analyse_percentage_totals.json')
    with open(json_path, 'r') as f:
        entries = json.load(f)

    totals = {
        "hc": {"all": {"energy_imported": 3500}},
        "cp": {
            "cp1": {"energy_imported": 18500},
            "cp2": {"energy_imported": 29000},
            "cp3": {"energy_imported": 11433}
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892},
            "counter1": {"grid": False, "energy_imported": 10000},
            "counter2": {"grid": False, "energy_imported": 8735}
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


def test_calc_energy_imported_by_source_message_filtering():
    """Test message filtering when component is in fault state and name is missing."""
    # setup
    entry = {
        "timestamp": 1234567890,
        "energy_source": {"grid": 0.6523, "pv": 0.2487, "bat": 0.0789, "cp": 0.0201},
        "cp": {
            "cp1": {"energy_imported": 15723.4, "fault_state": 0},
            "cp2": {"energy_imported": 22108.7, "fault_state": 2}  # fault state
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892.3, "fault_state": 0},
            "counter1": {"grid": False, "energy_imported": 8956.7, "fault_state": 2}  # fault state
        }
    }

    # Names dict is missing keys for cp2 and counter1
    names = {
        "cp1": "Ladepunkt 1",
        "counter0": "EVU-Zähler"
        # cp2 and counter1 intentionally missing
    }

    # execution - filter messages only for cp2
    result, message = calc_energy_imported_by_source(entry, names, message_key_filter="cp2")

    # evaluation
    # Should only get message for cp2, not counter1 (due to filtering)
    expected_message = ("Die Anteile der Energiequellen für Ladepunkt cp2 konnten nicht berechnet werden, da er sich "
                        "im Fehlerzustand befindet. Die Verbräuche werden mit 0 kWh angesetzt.\n")
    assert message == expected_message

    # cp2 should have zero values for all energy sources due to fault state
    assert result["cp"]["cp2"]["energy_imported_grid"] == 0
    assert result["cp"]["cp2"]["energy_imported_pv"] == 0
    assert result["cp"]["cp2"]["energy_imported_bat"] == 0
    assert result["cp"]["cp2"]["energy_imported_cp"] == 0

    # cp1 should have normal calculated values (not in fault state)
    assert result["cp"]["cp1"]["energy_imported_grid"] == 10256.374

    # counter1 should have zero values but no message (filtered out)
    assert result["counter"]["counter1"]["energy_imported_grid"] == 0
    assert result["counter"]["counter1"]["energy_imported_pv"] == 0
    assert result["counter"]["counter1"]["energy_imported_bat"] == 0
    assert result["counter"]["counter1"]["energy_imported_cp"] == 0


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
