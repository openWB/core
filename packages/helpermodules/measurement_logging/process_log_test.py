from copy import deepcopy
from unittest.mock import Mock
import pytest

from helpermodules.measurement_logging import process_log
from helpermodules.measurement_logging.process_log import (
    analyse_percentage,
    _calculate_average_power,
    process_entry,
    get_totals,
    CalculationType)

from helpermodules.measurement_logging.process_log_testdata import (counter_jumps_forward,
                                                                    counter_jumps_forward_processed,
                                                                    regular_daily_log_entry,
                                                                    regular_daily_log_entry_processed)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    entries = deepcopy(daily_log_sample)
    totals = get_totals(entries)

    # evaluation
    assert totals == daily_log_totals


def test_analyse_percentage(daily_log_entry_kw_percentage):
    # setup
    expected = deepcopy(daily_log_entry_kw_percentage)
    expected.update({"energy_source":  {'bat': 0.2398, 'cp': 0.0, 'grid': 0.6504, 'pv': 0.1098}})
    expected["cp"]["all"].update({
        "energy_imported_bat": 0.23,
        "energy_imported_cp": 0.0,
        "energy_imported_grid": 0.624,
        "energy_imported_pv": 0.105})
    expected["hc"]["all"].update({
        "energy_imported_bat": 0.002,
        "energy_imported_cp": 0.0,
        "energy_imported_grid": 0.007,
        "energy_imported_pv": 0.001})

    # execution
    entry = analyse_percentage(daily_log_entry_kw_percentage)

    # evaluation
    assert entry == expected


def test_convert_value_to_kW():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1800


def test_convert(daily_log_entry_kw, daily_log_sample):
    # setup and execution
    entry = process_entry(daily_log_sample[0], daily_log_sample[1], CalculationType.ALL)

    # evaluation
    assert entry == daily_log_entry_kw


@pytest.mark.parametrize("data, expected", [
    pytest.param(counter_jumps_forward, counter_jumps_forward_processed, id="counter jumps forward"),
    pytest.param(regular_daily_log_entry, regular_daily_log_entry_processed, id="regular daily log entry")
])
def test_get_daily_log(data, expected, monkeypatch):
    # setup
    collect_daily_log_data_mock = Mock(return_value=data)
    monkeypatch.setattr(process_log, "_collect_daily_log_data", collect_daily_log_data_mock)

    # execution
    daily_log_processed = process_log.get_daily_log("20250616")

    # evaluation
    assert daily_log_processed == expected
