from copy import deepcopy
from helpermodules.measurement_logging.process_log import (
    analyse_percentage,
    _calculate_average_power,
    process_entry,
    get_totals,
    CalculationType)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    totals = get_totals(daily_log_sample)

    # evaluation
    assert totals == daily_log_totals


def test_analyse_percentage(daily_log_entry_kw):
    # setup
    expected = deepcopy(daily_log_entry_kw)
    expected.update({"power_source":  {'bat': 0.24, 'cp': 0.0, 'grid': 0.6502, 'pv': 0.1098}})

    # execution
    entry = analyse_percentage(daily_log_entry_kw)

    # evaluation
    assert entry == expected


def test_convert_value_to_kW():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1.8


def test_convert(daily_log_entry_kw, daily_log_sample):
    # setup and execution
    entry = process_entry(daily_log_sample[0], daily_log_sample[1], CalculationType.ALL)

    # evaluation
    assert entry == daily_log_entry_kw
