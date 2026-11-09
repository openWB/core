import fcntl
from unittest.mock import Mock

import pytest

from helpermodules.measurement_logging import generate_totals_subprocess


@pytest.mark.parametrize("fails", [False, True])
def test_generate_totals_cleans_up_lock_after_processing(monkeypatch, tmp_path, fails):
    # setup
    lock_file = tmp_path / "locks" / "generate_totals.lock"
    monkeypatch.setattr(generate_totals_subprocess, "LOCK_FILE", lock_file)

    generate_mock = Mock(side_effect=RuntimeError("generator failed") if fails else None)

    monkeypatch.setattr(generate_totals_subprocess, "_generate_totals", generate_mock)

    # execution
    if fails:
        with pytest.raises(RuntimeError, match="generator failed"):
            generate_totals_subprocess.generate_totals()
    else:
        generate_totals_subprocess.generate_totals()

    # evaluation
    generate_mock.assert_called_once()
    assert lock_file.parent.is_dir()
    assert not lock_file.exists()


def test_generate_totals_fails_when_lock_is_not_acquired(monkeypatch, tmp_path):
    # setup
    lock_file = tmp_path / "locks" / "generate_totals.lock"
    monkeypatch.setattr(generate_totals_subprocess, "LOCK_FILE", lock_file)

    generate_mock = Mock()

    monkeypatch.setattr(generate_totals_subprocess, "_generate_totals", generate_mock)

    # execution
    lock_file.parent.mkdir(parents=True)
    with lock_file.open("a") as held_lock:
        fcntl.flock(held_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            generate_totals_subprocess.generate_totals()

    # evaluation
    generate_mock.assert_not_called()
    assert lock_file.parent.is_dir()
    assert lock_file.exists()


@pytest.mark.parametrize("replaced", [False, True])
def test_generate_totals_aborts_if_lock_disappears_or_is_replaced_before_processing(monkeypatch, tmp_path, replaced):
    lock_file = tmp_path / "generate_totals.lock"
    monkeypatch.setattr(generate_totals_subprocess, "LOCK_FILE", lock_file)

    def change_lock(*args):
        if replaced:
            lock_file.rename(tmp_path / "old.lock")
            lock_file.write_text("other process")
        else:
            lock_file.unlink()

    monkeypatch.setattr(generate_totals_subprocess.fcntl, "flock", change_lock)
    generate_mock = Mock()
    monkeypatch.setattr(generate_totals_subprocess, "_generate_totals", generate_mock)

    message = "ausgetauscht" if replaced else "gelöscht"
    with pytest.raises(RuntimeError, match=message) as error:
        generate_totals_subprocess.generate_totals()

    generate_mock.assert_not_called()
    if replaced:
        assert lock_file.read_text() == "other process"
    else:
        assert isinstance(error.value.__cause__, FileNotFoundError)
        assert not lock_file.exists()


@pytest.mark.parametrize("replaced", [False, True])
def test_generate_totals_cleanup_handles_changed_lock(monkeypatch, tmp_path, replaced):
    lock_file = tmp_path / "generate_totals.lock"
    monkeypatch.setattr(generate_totals_subprocess, "LOCK_FILE", lock_file)

    def generate():
        if replaced:
            lock_file.rename(tmp_path / "old.lock")
            lock_file.write_text("other process")
        else:
            lock_file.unlink()

    monkeypatch.setattr(generate_totals_subprocess, "_generate_totals", generate)

    generate_totals_subprocess.generate_totals()

    if replaced:
        assert lock_file.read_text() == "other process"
    else:
        assert not lock_file.exists()


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
