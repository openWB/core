from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

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
        process.communicate.side_effect = [subprocess.TimeoutExpired("client", 5), (None, "")]
    else:
        process.communicate.return_value = None, ""
    monkeypatch.setattr(api.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(api, "get_executable_path", Mock(return_value="client"))
    monkeypatch.setattr(api, "BrokerClient", Mock(return_value=broker))
    monkeypatch.setattr(Path, "touch", Mock())
    # Expose the callbacks without creating value stores or publishing IO states.
    monkeypatch.setattr(api, "ConfigurableIo", lambda **kwargs: SimpleNamespace(**kwargs))
    io = api.create_io(Eebus(id=3))
    io.initializer()

    io.shutdown_handler()

    process.terminate.assert_called_once_with()
    if termination_times_out:
        process.kill.assert_called_once_with()
    else:
        process.kill.assert_not_called()
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
    process.communicate.return_value = None, "connection failed"
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
    process.wait.assert_not_called()
    process.communicate.assert_not_called()


@pytest.mark.parametrize(
    "returncode, message",
    [(2, "Zertifikat oder Key ungültig"), (5, "Fehlercode: 5, Fehler: connection failed")],
)
def test_exited_client_is_restarted_and_failure_reported(client_io, returncode, message):
    io, process = client_io
    process.poll.return_value = returncode

    with pytest.raises(ValueError, match=message):
        io.component_reader()

    assert api.subprocess.Popen.call_count == 2
    process.communicate.assert_called_once_with()


def test_successfully_exited_client_is_restarted(client_io):
    io, process = client_io
    process.poll.return_value = 0

    io.component_reader()

    assert api.subprocess.Popen.call_count == 2
