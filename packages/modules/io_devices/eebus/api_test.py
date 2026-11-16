from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from modules.io_devices.eebus import api
from modules.io_devices.eebus.config import CertInfo, Eebus, EebusConfiguration


def test_new_certificate_publishes_changed_config_without_mutating_active_config(monkeypatch, tmp_path, mock_pub):
    config = Eebus(id=3, configuration=EebusConfiguration(cert_info=CertInfo(client_ski="old-ski")))
    monkeypatch.setattr(api.data, "data", SimpleNamespace(system_data={"io3": SimpleNamespace(config=config)}),
                        raising=False)
    monkeypatch.setattr(api, "cert_path", str(tmp_path))
    monkeypatch.setattr(api, "run_command", Mock(side_effect=["", "Subject Key Identifier\n    AA:BB:CC"]))

    api.create_pub_cert_ski(3)

    assert config.configuration.cert_info.client_ski == "old-ski"
    topic, payload = mock_pub.pub.call_args.args
    assert topic == "openWB/set/system/io/3/config"
    assert payload["configuration"]["cert_info"]["client_ski"] == "AABBCC"
    assert (tmp_path / "ski-3").read_text() == "AABBCC"


def test_failed_certificate_generation_does_not_publish_config(monkeypatch, tmp_path, mock_pub):
    monkeypatch.setattr(api, "cert_path", str(tmp_path))
    monkeypatch.setattr(api, "run_command", Mock(side_effect=subprocess.CalledProcessError(1, "openssl")))

    with pytest.raises(subprocess.CalledProcessError):
        api.create_pub_cert_ski(3)

    mock_pub.pub.assert_not_called()
    assert not (tmp_path / "ski-3").exists()


@pytest.mark.parametrize("termination_times_out", [False, True])
def test_shutdown_waits_for_client_and_disconnects_broker(monkeypatch, termination_times_out):
    broker = Mock()
    process = Mock()
    process.poll.return_value = None
    if termination_times_out:
        process.wait.side_effect = [subprocess.TimeoutExpired("client", 5), 0]
    monkeypatch.setattr(api.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(api, "get_executable_path", Mock(return_value="client"))
    monkeypatch.setattr(api, "BrokerClient", Mock(return_value=broker))
    monkeypatch.setattr(Path, "touch", Mock())
    monkeypatch.setattr("modules.common.configurable_io.store.get_io_value_store", Mock())
    io = api.create_io(Eebus(id=3))

    io.shutdown()

    process.terminate.assert_called_once_with()
    if termination_times_out:
        process.kill.assert_called_once_with()
        assert process.wait.call_args_list == [call(timeout=5), call()]
    else:
        process.kill.assert_not_called()
        process.wait.assert_called_once_with(timeout=5)
    process.communicate.assert_not_called()
    broker.disconnect.assert_called_once_with()
    with pytest.raises(RuntimeError, match="EEBus-Client wurde beendet"):
        io.component_reader()
    assert api.subprocess.Popen.call_count == 1


@pytest.fixture
def client_io(monkeypatch):
    broker_factory = Mock()
    monkeypatch.setattr(api, "get_executable_path", Mock(return_value="client"))
    monkeypatch.setattr(api, "BrokerClient", broker_factory)
    monkeypatch.setattr(Path, "touch", Mock())
    monkeypatch.setattr(api, "ConfigurableIo", lambda **kwargs: SimpleNamespace(**kwargs))
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(api.subprocess, "Popen", Mock(return_value=process))
    io = api.create_io(Eebus(id=3))
    io.initializer()
    on_message = broker_factory.call_args.args[2]
    on_message(None, None, Mock(topic="openWB/eebus/3/get/fault_state", payload=b"0"))
    try:
        yield io, process
    finally:
        io.shutdown_handler()


def test_running_client_is_only_polled_without_waiting(client_io):
    io, process = client_io

    io.component_reader()
    io.component_reader()

    assert api.subprocess.Popen.call_count == 1
    assert process.poll.call_args_list == [call(), call()]
    process.wait.assert_not_called()
    process.communicate.assert_not_called()


@pytest.mark.parametrize(
    "returncode, message",
    [(2, "Zertifikat oder Key ungültig"), (5, "EEBus-Client beendet mit Fehlercode: 5")],
)
def test_exited_client_is_restarted_and_failure_reported(client_io, returncode, message):
    io, process = client_io
    process.poll.return_value = returncode

    with pytest.raises(ValueError, match=message):
        io.component_reader()

    assert api.subprocess.Popen.call_count == 2
    process.communicate.assert_not_called()


def test_successfully_exited_client_is_restarted(client_io):
    io, process = client_io
    process.poll.return_value = 0

    io.component_reader()

    assert api.subprocess.Popen.call_count == 2


@pytest.mark.parametrize("failure", ["missing", "permission"])
def test_start_failure_keeps_broker_initialized_and_read_retries(monkeypatch, failure):
    broker = Mock()
    broker_factory = Mock(return_value=broker)
    process = Mock()
    process.poll.return_value = None
    popen = Mock(return_value=process)
    executable = Mock(return_value="client")
    if failure == "missing":
        executable.side_effect = [None, "client"]
    else:
        popen.side_effect = [PermissionError("not executable"), process]
    monkeypatch.setattr(api, "get_executable_path", executable)
    monkeypatch.setattr(api.subprocess, "Popen", popen)
    monkeypatch.setattr(api, "BrokerClient", broker_factory)
    monkeypatch.setattr(Path, "touch", Mock())
    value_store = Mock()
    monkeypatch.setattr("modules.common.configurable_io.store.get_io_value_store", Mock(return_value=value_store))

    io = api.create_io(Eebus(id=3))

    assert io.fault_state.fault_state != 0
    broker_factory.assert_called_once()
    broker_factory.call_args.args[2](None, None, Mock(topic="openWB/eebus/3/get/fault_state", payload=b"0"))
    try:
        io.read()

        assert io.fault_state.fault_state == 0
        value_store.set.assert_called_once()
        broker.start_finite_loop.assert_called_once()
    finally:
        io.shutdown()


def test_failed_restart_can_be_retried(client_io, monkeypatch):
    io, process = client_io
    process.poll.return_value = 5
    popen = Mock(side_effect=[PermissionError("not executable"), process])
    monkeypatch.setattr(api.subprocess, "Popen", popen)

    with pytest.raises(PermissionError):
        io.component_reader()
    process.poll.return_value = None
    io.component_reader()

    assert popen.call_count == 2


def test_large_stderr_does_not_block_client(monkeypatch):
    real_popen = subprocess.Popen
    processes = []

    def start_client(args, **kwargs):
        process = real_popen(
            [sys.executable, "-c", "import sys; sys.stderr.write('x' * 1048576 + 'END'); sys.exit(5)"], **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(api.subprocess, "Popen", start_client)
    monkeypatch.setattr(api, "get_executable_path", Mock(return_value="client"))
    monkeypatch.setattr(api, "BrokerClient", Mock())
    monkeypatch.setattr(Path, "touch", Mock())
    monkeypatch.setattr("modules.common.configurable_io.store.get_io_value_store", Mock())
    io = api.create_io(Eebus(id=3))
    try:
        assert processes[0].wait(timeout=5) == 5
        with pytest.raises(ValueError, match="EEBus-Client beendet mit Fehlercode: 5"):
            io.component_reader()
    finally:
        io.shutdown()
