import os
from pathlib import Path
import subprocess
from unittest.mock import Mock

import pytest

from modules.vehicles.nissanconnect import connection_test
from modules.vehicles.nissanconnect.tools import probe
from modules.vehicles.nissanconnect.src.api import BatteryStatus


@pytest.fixture
def local_terminal(monkeypatch):
    for name in ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(probe.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(probe.sys.stdout, "isatty", lambda: True)
    # Do not change the test process's global logging state.
    monkeypatch.setattr(probe.logging, "disable", Mock())


def test_probe_refuses_agent_context(monkeypatch, local_terminal):
    monkeypatch.setenv("CODEX_THREAD_ID", "synthetic-agent-session")
    credentials = Mock(side_effect=AssertionError("Credentials must not be requested"))
    monkeypatch.setattr(probe, "getpass", credentials)
    assert probe.main() == 2
    credentials.assert_not_called()


def test_probe_refuses_redirected_output(monkeypatch, local_terminal):
    monkeypatch.setattr(probe.sys.stdout, "isatty", lambda: False)
    assert probe.main() == 2


def test_probe_aborts_before_requesting_credentials(monkeypatch, local_terminal):
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    credentials = Mock()
    monkeypatch.setattr(probe, "getpass", credentials)
    assert probe.main() == 0
    credentials.assert_not_called()


def test_probe_uses_hidden_inputs_without_echo(monkeypatch, local_terminal, capsys):
    monkeypatch.setattr(probe.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr(probe, "getpass", Mock(side_effect=["synthetic@example.invalid", "synthetic-password", ""]))
    client = Mock()
    client.fetch_battery.return_value = BatteryStatus(47, 1640995200, 123, 12345.6)
    factory = Mock(return_value=client)
    monkeypatch.setattr(probe, "NissanClient", factory)
    assert probe.main() == 0
    output = capsys.readouterr().out
    assert "synthetic@example.invalid" not in output
    assert "synthetic-password" not in output
    assert "SoC: 47 %" in output
    assert "Odometer: 12345.6 km (measurement time unavailable)" in output
    client.fetch_battery.assert_called_once_with(include_odometer=True)


def test_probe_aborts_if_hidden_input_is_unavailable(monkeypatch, local_terminal):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr(probe, "getpass", Mock(side_effect=probe.GetPassWarning("synthetic")))
    factory = Mock()
    monkeypatch.setattr(probe, "NissanClient", factory)
    assert probe.main() == 2
    factory.assert_not_called()


@pytest.mark.parametrize("entrypoint,script_path,expected_exit_code,expected_output", [
    (probe, "tools/probe.py", 2,
     "Aborted: Please run in a private terminal outside a Codex or agent session."),
    (connection_test, "connection_test.py", 0,
     '{"success": false, "code": "agent_environment"}'),
])
def test_direct_entrypoint_with_isolated_python_loads_internal_api(
        tmp_path, entrypoint, script_path, expected_exit_code, expected_output):
    # Exercise both supported direct-start locations with a synthetic API only.
    # A missing or incorrect import must fail before the agent guard can return.
    (tmp_path / "src").mkdir()
    (tmp_path / "src/__init__.py").write_text("", encoding="utf-8")
    script = tmp_path / script_path
    script.parent.mkdir(exist_ok=True)
    script.write_text(Path(entrypoint.__file__).read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "src/api.py").write_text(
        'class NissanError(Exception): pass\n'
        'class AuthenticationError(NissanError): pass\n'
        'class RateLimitError(NissanError): pass\n'
        'VIN_PATTERN = "synthetic"\n'
        'class NissanClient:\n'
        '    def __init__(self, *args, **kwargs):\n'
        '        raise AssertionError("No real client in the startup test")\n',
        encoding="utf-8")
    result = subprocess.run(
        [probe.sys.executable, "-I", "-B", str(script)], cwd=str(tmp_path),
        env=dict(os.environ, CODEX_CI="1"), capture_output=True, text=True, timeout=10)
    assert result.returncode == expected_exit_code, result.stderr
    assert result.stdout.strip() == expected_output
    assert result.stderr == ""
