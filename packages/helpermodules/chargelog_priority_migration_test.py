import json
from unittest.mock import Mock

import pytest

from helpermodules import update_config
from helpermodules.update_config import UpdateConfig


def make_update_config(tmp_path):
    config = UpdateConfig()
    config.base_path = tmp_path
    config.all_received_topics = {
        "openWB/system/file_operation_version": [0],
    }
    return config


def test_charge_log_priority_migration_preserves_numbers_and_is_idempotent(tmp_path, monkeypatch):
    config = make_update_config(tmp_path)
    directory = tmp_path / "data" / "charge_log"
    directory.mkdir(parents=True)
    entries = [
        {"vehicle": {"prio": value}, "data": {"costs": 1.23}}
        for value in (True, False, 1, 2, 7, None, "1")
    ] + [{"vehicle": {}}, {}, {"vehicle": None}]
    path = directory / "202610.json"
    path.write_text(json.dumps(entries))
    untouched = directory / "202609.json"
    untouched.write_text('[{"vehicle": {"prio": 3}}]')
    original_untouched = untouched.read_bytes()

    config.upgrade_file_operation_1()

    migrated = json.loads(path.read_text())
    assert [entry["vehicle"]["prio"] for entry in migrated[:7]] == [1, 2, 1, 2, 7, None, "1"]
    assert all(type(entry["vehicle"]["prio"]) is int for entry in migrated[:5])
    assert all(entry["data"] == {"costs": 1.23} for entry in migrated[:7])
    assert migrated[7:] == entries[7:]
    assert untouched.read_bytes() == original_untouched
    assert config.all_received_topics["openWB/system/file_operation_version"] == [0, 1]

    writer = Mock(side_effect=AssertionError("Bereits migrierte Dateien dürfen nicht erneut geschrieben werden."))
    monkeypatch.setattr(update_config, "write_and_check", writer)
    config.upgrade_file_operation_1()
    writer.assert_not_called()


def test_charge_log_priority_migration_without_files(tmp_path):
    config = make_update_config(tmp_path)
    config.upgrade_file_operation_1()
    assert config.all_received_topics["openWB/system/file_operation_version"] == [0, 1]


def test_charge_log_priority_migration_runs_once_via_regular_file_upgrade(tmp_path, monkeypatch):
    config = make_update_config(tmp_path)
    config.all_received_topics["openWB/system/log_data_ready"] = True
    directory = tmp_path / "data" / "charge_log"
    directory.mkdir(parents=True)
    path = directory / "202610.json"
    path.write_text('[{"vehicle": {"prio": true}}]')
    migration = Mock(wraps=config.upgrade_file_operation_1)
    monkeypatch.setattr(config, "upgrade_file_operation_1", migration)

    config._UpdateConfig__solve_breaking_changes_filesystem()
    config._UpdateConfig__solve_breaking_changes_filesystem()

    migration.assert_called_once_with()
    assert type(json.loads(path.read_text())[0]["vehicle"]["prio"]) is int
    assert config.all_received_topics["openWB/system/file_operation_version"] == [0, 1]


@pytest.mark.parametrize("content", ["{broken", '{"entries": []}'])
def test_charge_log_priority_migration_retries_failed_files(tmp_path, content):
    config = make_update_config(tmp_path)
    directory = tmp_path / "data" / "charge_log"
    directory.mkdir(parents=True)
    path = directory / "202610.json"
    path.write_text(content)

    with pytest.raises(RuntimeError):
        config.upgrade_file_operation_1()

    assert path.read_text() == content
    assert config.all_received_topics["openWB/system/file_operation_version"] == [0]
    path.write_text('[{"vehicle": {"prio": false}}]')
    config.upgrade_file_operation_1()
    assert json.loads(path.read_text())[0]["vehicle"]["prio"] == 2
    assert config.all_received_topics["openWB/system/file_operation_version"] == [0, 1]


def test_charge_log_priority_migration_detects_failed_write_of_true_to_one(tmp_path, monkeypatch):
    config = make_update_config(tmp_path)
    directory = tmp_path / "data" / "charge_log"
    directory.mkdir(parents=True)
    path = directory / "202610.json"
    path.write_text('[{"vehicle": {"prio": true}}]')
    monkeypatch.setattr(update_config, "write_and_check", Mock())

    with pytest.raises(RuntimeError):
        config.upgrade_file_operation_1()

    assert json.loads(path.read_text())[0]["vehicle"]["prio"] is True
    assert config.all_received_topics["openWB/system/file_operation_version"] == [0]
