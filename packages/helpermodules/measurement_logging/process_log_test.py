from helpermodules.measurement_logging.conftest import POWER_SOURCE_TOTALS, SAMPLE, TOTALS
from helpermodules.measurement_logging.process_log import _analyse_percentage, _convert_value_to_kW, get_totals


def test_get_totals():
    # setup and execution
    totals = get_totals(SAMPLE)

    # evaluation
    assert totals == TOTALS


def test_analyse_percentage():
    # setup and execution
    entry = _analyse_percentage(TOTALS)

    # evaluation
    assert entry == POWER_SOURCE_TOTALS


def test_convert_value_to_kW():
    # setup and execution
    power = _convert_value_to_kW(100, 250, 300)

    # evaluation
    assert power == 1.8
