from unittest.mock import Mock

from helpermodules.measurement_logging import generate_totals_subprocess


def test_generate_totals_calls_generator_when_lock_is_acquired(monkeypatch, tmp_path):
    # setup
    lock_file = tmp_path / "locks" / "generate_totals.lock"
    monkeypatch.setattr(generate_totals_subprocess, "LOCK_FILE", lock_file)

    flock_mock = Mock()
    generate_mock = Mock()

    monkeypatch.setattr(generate_totals_subprocess.fcntl, "flock", flock_mock)
    monkeypatch.setattr(generate_totals_subprocess, "_generate_totals", generate_mock)

    # execution
    generate_totals_subprocess.generate_totals()

    # evaluation
    flock_mock.assert_called_once()
    generate_mock.assert_called_once()
    assert lock_file.parent.is_dir()


def test_generate_totals_skips_generator_when_lock_is_not_acquired(monkeypatch, tmp_path):
    # setup
    lock_file = tmp_path / "locks" / "generate_totals.lock"
    monkeypatch.setattr(generate_totals_subprocess, "LOCK_FILE", lock_file)

    flock_mock = Mock(side_effect=RuntimeError("already locked"))
    generate_mock = Mock()

    monkeypatch.setattr(generate_totals_subprocess.fcntl, "flock", flock_mock)
    monkeypatch.setattr(generate_totals_subprocess, "_generate_totals", generate_mock)

    # execution
    generate_totals_subprocess.generate_totals()

    # evaluation
    flock_mock.assert_called_once()
    generate_mock.assert_not_called()
    assert lock_file.parent.is_dir()
