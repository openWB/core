from unittest.mock import Mock

from helpermodules.measurement_logging import process_log


pytest_plugins = ["helpermodules.measurement_logging.process_log_testdata"]


def test_get_daily_log_counter_jump(counter_jumps_forward, counter_jumps_forward_processed, monkeypatch):
    # setup
    collect_daily_log_data_mock = Mock(return_value=counter_jumps_forward)
    monkeypatch.setattr(process_log, "_collect_daily_log_data", collect_daily_log_data_mock)

    # execution
    daily_log_processed = process_log.get_daily_log("20250616")

    # evaluation
    assert daily_log_processed == counter_jumps_forward_processed


def test_get_daily_log_regular(regular_daily_log_entry, regular_daily_log_entry_processed, monkeypatch):
    # setup
    collect_daily_log_data_mock = Mock(return_value=regular_daily_log_entry)
    monkeypatch.setattr(process_log, "_collect_daily_log_data", collect_daily_log_data_mock)

    # execution
    daily_log_processed = process_log.get_daily_log("20250616")

    # evaluation
    assert daily_log_processed == regular_daily_log_entry_processed
