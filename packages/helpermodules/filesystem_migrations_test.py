import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from paho.mqtt.client import MQTTMessage

from helpermodules import filesystem_migrations
from helpermodules.filesystem_migrations import FilesystemMigrations


@pytest.mark.parametrize("file_operation_version, finished, expected_calls", [
    ([], False, 1),
    ([0], True, 0),
    ([0], False, 1),
    (None, None, 1),
])
def test_file_operation_0_start_behavior(monkeypatch, file_operation_version, finished, expected_calls):
    monkeypatch.setattr(FilesystemMigrations, "FILE_OPERATION_VERSION", 0)
    updater = FilesystemMigrations()
    updater.all_received_topics = {
        "openWB/system/file_operation_version": file_operation_version,
        "openWB/system/log_data_ready": finished,
    }

    with patch.object(updater, "upgrade_file_operation_0") as upgrade_mock:
        updater._FilesystemMigrations__solve_breaking_changes_filesystem()
    assert upgrade_mock.call_count == expected_calls


@pytest.mark.parametrize("progress", [0, 1, 2])
def test_legacy_integer_progress_is_persisted_as_list_and_pending_migrations_run(monkeypatch, mock_pub, progress):
    updater = FilesystemMigrations()
    updater.all_received_topics = {
        "openWB/system/file_operation_version": str(progress).encode(),
        "openWB/system/log_data_ready": b"true",
    }
    monkeypatch.setattr(FilesystemMigrations, "FILE_OPERATION_VERSION", 2)
    calls = []
    for version in range(3):
        monkeypatch.setattr(
            updater, f"upgrade_file_operation_{version}",
            lambda version=version: calls.append(version), raising=False,
        )

    updater._FilesystemMigrations__solve_breaking_changes_filesystem()

    assert calls == list(range(progress, 3))
    assert updater.all_received_topics["openWB/system/file_operation_version"] == [0, 1, 2]
    first_publish = mock_pub.publisher.client.publish.call_args_list[0]
    assert first_publish.args == ("openWB/system/file_operation_version", json.dumps(list(range(progress))))
    assert first_publish.kwargs == {"qos": 1, "retain": True}


def test_file_operations_run_sequentially_and_resume_after_failure(monkeypatch):
    fails = True
    updater = FilesystemMigrations()
    updater.all_received_topics = {
        "openWB/system/file_operation_version": [0],
        "openWB/system/log_data_ready": True,
    }
    monkeypatch.setattr(FilesystemMigrations, "FILE_OPERATION_VERSION", 3)
    calls = []

    def migration_1():
        assert updater.all_received_topics["openWB/system/file_operation_version"] == [0]
        calls.append(1)

    def migration_2():
        assert updater.all_received_topics["openWB/system/file_operation_version"] == [0, 1]
        calls.append(2)
        if fails:
            raise RuntimeError("migration failed")

    def migration_3():
        assert updater.all_received_topics["openWB/system/file_operation_version"] == [0, 1, 2]
        calls.append(3)

    monkeypatch.setattr(updater, "upgrade_file_operation_1", migration_1, raising=False)
    monkeypatch.setattr(updater, "upgrade_file_operation_2", migration_2, raising=False)
    monkeypatch.setattr(updater, "upgrade_file_operation_3", migration_3, raising=False)

    with pytest.raises(RuntimeError, match="migration failed"):
        updater._FilesystemMigrations__solve_breaking_changes_filesystem()
    assert calls == [1, 2]
    assert updater.all_received_topics["openWB/system/file_operation_version"] == [0, 1]
    fails = False
    updater._FilesystemMigrations__solve_breaking_changes_filesystem()
    assert calls == [1, 2, 2, 3]

    assert updater.all_received_topics["openWB/system/file_operation_version"] == [0, 1, 2, 3]


def test_file_operation_stops_if_version_cannot_be_published(monkeypatch, mock_pub):
    monkeypatch.setattr(FilesystemMigrations, "FILE_OPERATION_VERSION", 1)
    updater = FilesystemMigrations()
    updater.all_received_topics = {
        "openWB/system/file_operation_version": [],
        "openWB/system/log_data_ready": True,
    }
    monkeypatch.setattr(updater, "upgrade_file_operation_0", Mock())
    next_migration = Mock()
    monkeypatch.setattr(updater, "upgrade_file_operation_1", next_migration, raising=False)
    mock_pub.publisher.client.publish.return_value.is_published.return_value = False

    with pytest.raises(TimeoutError, match="konnte nicht gespeichert"):
        updater._FilesystemMigrations__solve_breaking_changes_filesystem()

    assert updater.all_received_topics["openWB/system/file_operation_version"] == []
    next_migration.assert_not_called()


def test_next_migration_runs_after_all_totals_attempts_despite_failed_day(monkeypatch, mock_pub):
    monkeypatch.setattr(FilesystemMigrations, "FILE_OPERATION_VERSION", 1)
    from helpermodules.measurement_logging import generate_totals_subprocess

    updater = FilesystemMigrations()
    updater.all_received_topics = {
        "openWB/system/file_operation_version": [],
        "openWB/system/log_data_ready": False,
    }
    days = [Path("20220101.json"), Path("20220102.json")]
    monkeypatch.setattr(generate_totals_subprocess, "get_all_days_to_calc", lambda: days)
    daily = Mock(side_effect=[RuntimeError("broken log"), {}])
    monthly = Mock(return_value={})
    monkeypatch.setattr(generate_totals_subprocess, "save_daily_source_totals", daily)
    monkeypatch.setattr(generate_totals_subprocess, "save_monthly_source_totals", monthly)
    monkeypatch.setattr(filesystem_migrations, "generate_totals", generate_totals_subprocess._generate_totals)

    def next_migration():
        assert daily.call_count == 2
        monthly.assert_called_once_with("202201", saving=True)
        assert updater.all_received_topics["openWB/system/log_data_ready"] is True
        assert updater.all_received_topics["openWB/system/file_operation_version"] == [0]
        assert any(call.args == ("openWB/system/log_data_ready", "true")
                   for call in mock_pub.publisher.client.publish.call_args_list)

    next_operation = Mock(side_effect=next_migration)
    monkeypatch.setattr(updater, "upgrade_file_operation_1", next_operation, raising=False)

    updater._FilesystemMigrations__solve_breaking_changes_filesystem()

    next_operation.assert_called_once_with()
    assert updater.all_received_topics["openWB/system/file_operation_version"] == [0, 1]


@pytest.mark.parametrize("completed, ready", [([], True), ([0], False)])
def test_file_operation_0_failure_leaves_logs_unready_and_blocks_next(monkeypatch, mock_pub, completed, ready):
    monkeypatch.setattr(FilesystemMigrations, "FILE_OPERATION_VERSION", 1)
    updater = FilesystemMigrations()
    updater.all_received_topics = {
        "openWB/system/file_operation_version": completed,
        "openWB/system/log_data_ready": ready,
    }
    monkeypatch.setattr(
        filesystem_migrations, "generate_totals", Mock(side_effect=RuntimeError("generator failed")))
    next_migration = Mock()
    monkeypatch.setattr(updater, "upgrade_file_operation_1", next_migration, raising=False)

    with pytest.raises(RuntimeError, match="generator failed"):
        updater._FilesystemMigrations__solve_breaking_changes_filesystem()

    assert updater.all_received_topics["openWB/system/log_data_ready"] is False
    assert updater.all_received_topics["openWB/system/file_operation_version"] == completed
    mock_pub.publisher.client.publish.assert_called_once_with(
        "openWB/system/log_data_ready", "false", qos=1, retain=True)
    next_migration.assert_not_called()


def test_filesystem_worker_reads_current_topics_before_migrating(monkeypatch):
    updater = FilesystemMigrations()
    broker = Mock()
    broker_client = Mock(return_value=broker)
    monkeypatch.setattr(filesystem_migrations, "BrokerClient", broker_client)
    topics = {
        "openWB/system/file_operation_version": b"[0]",
        "openWB/system/log_data_ready": b"true",
    }

    def read_topics():
        on_message = broker_client.call_args.args[2]
        for topic, payload in topics.items():
            message = MQTTMessage(topic=topic.encode())
            message.payload = payload
            on_message(broker.client, None, message)
        assert updater.all_received_topics == topics

    broker.start_finite_loop.side_effect = read_topics
    migration = Mock()
    monkeypatch.setattr(updater, "upgrade_file_operation_0", migration)

    updater.update_filesystem()

    migration.assert_not_called()
    broker.start_finite_loop.assert_called_once_with()
    broker.disconnect.assert_called_once_with()
