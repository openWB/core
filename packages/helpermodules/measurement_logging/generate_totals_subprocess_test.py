from unittest.mock import Mock

import pytest

from helpermodules.measurement_logging import generate_totals_subprocess


@pytest.mark.parametrize("failure", [None, RuntimeError("broken log")])
@pytest.mark.parametrize("period", ["daily", "monthly"])
def test_generate_totals_continues_after_failed_logs(monkeypatch, mock_pub, period, failure):
    days = [generate_totals_subprocess.Path(f"20220{month}01.json") for month in range(1, 4)]
    monkeypatch.setattr(generate_totals_subprocess, "get_all_days_to_calc", lambda: days)
    daily = Mock(return_value={})
    monthly = Mock(return_value={})
    failed = daily if period == "daily" else monthly
    failed.side_effect = [failure, {}, {}]
    log_error = Mock()
    monkeypatch.setattr(generate_totals_subprocess.log, "exception", log_error)
    monkeypatch.setattr(generate_totals_subprocess, "save_daily_source_totals", daily)
    monkeypatch.setattr(generate_totals_subprocess, "save_monthly_source_totals", monthly)

    def publish(*args, **kwargs):
        assert daily.call_count == 3
        assert monthly.call_count == 3
        return Mock()

    mock_pub.publisher.client.publish.side_effect = publish

    generate_totals_subprocess._generate_totals()

    assert daily.call_args_list == [((day.stem,), {"saving": True}) for day in days]
    assert monthly.call_args_list == [((f"20220{month}",), {"saving": True}) for month in range(1, 4)]
    assert log_error.call_count == (1 if failure is not None else 0)
    mock_pub.publisher.client.publish.assert_called_once_with(
        "openWB/system/log_data_ready", "true", qos=1, retain=True)
