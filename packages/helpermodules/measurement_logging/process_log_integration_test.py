from unittest.mock import Mock
import pytest

from helpermodules.measurement_logging import process_log

from helpermodules.measurement_logging.process_log_testdata import (counter_jumps_forward,
                                                                    counter_jumps_forward_processed,
                                                                    regular_daily_log_entry,
                                                                    regular_daily_log_entry_processed)


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
