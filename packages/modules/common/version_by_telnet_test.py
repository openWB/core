import socket
import builtins
import importlib
import sys
from threading import Event, Thread
from types import ModuleType
from unittest.mock import MagicMock, Mock

import pytest

from modules.common import version_by_telnet


def test_falls_back_to_stdlib_telnetlib_when_telnetlib3_is_missing(monkeypatch):
    stdlib_telnetlib = ModuleType("telnetlib")
    original_import = builtins.__import__

    def import_without_telnetlib3(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "telnetlib3":
            raise ModuleNotFoundError("No module named 'telnetlib3'", name="telnetlib3")
        return original_import(name, globals, locals, fromlist, level)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(builtins, "__import__", import_without_telnetlib3)
            patch.setitem(sys.modules, "telnetlib", stdlib_telnetlib)
            importlib.reload(version_by_telnet)
            assert version_by_telnet.telnetlib is stdlib_telnetlib
    finally:
        importlib.reload(version_by_telnet)


@pytest.fixture
def telnet_server():
    threads = []
    errors = []

    def start(payload: bytes, close_after_send: bool):
        listener = socket.socket()
        listener.settimeout(3)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        closed = Event()
        received = bytearray()

        def serve():
            try:
                with listener:
                    connection, _ = listener.accept()
                    with connection:
                        connection.settimeout(3)
                        if payload:
                            connection.sendall(payload)
                        if not close_after_send:
                            while True:
                                data = connection.recv(4096)
                                if not data:
                                    break
                                received.extend(data)
            except Exception as error:
                errors.append(error)
            finally:
                closed.set()

        thread = Thread(target=serve)
        threads.append(thread)
        thread.start()
        return port, closed, received

    yield start

    for thread in threads:
        thread.join(timeout=4)
        assert not thread.is_alive()
    assert not errors


@pytest.mark.parametrize("payload,expected,result,close_after_send", [
    (b"banner\r\nopenWB Satellit 2.0\r\ntrailing", "openWB Satellit 2.0", "openWB Satellit 2.0", False),
    (b"banner\r\nopenWB DimmModul\r\ntrailing", "openWB DimmModul", "openWB DimmModul", False),
    (b"\xff\xfb\x01banner\r\nopenWB DimmModul", "openWB DimmModul", "openWB DimmModul", False),
    (b"partial", "not-present", "partial", False),
    (b"", "not-present", "", False),
    (b"partial", "not-present", "partial", True),
])
def test_get_version_by_telnet(telnet_server, payload: bytes, expected: str, result: str, close_after_send: bool):
    port, closed, received = telnet_server(payload, close_after_send)

    assert version_by_telnet.get_version_by_telnet(expected, "127.0.0.1", port) == result
    assert closed.wait(timeout=4)
    if payload.startswith(b"\xff\xfb\x01"):
        assert b"\xff\xfe\x01" in received


def test_default_port_and_timeouts(monkeypatch):
    client = MagicMock()
    client.__enter__.return_value = client
    client.read_until.return_value = b"banner\r\nopenWB DimmModul"
    factory = Mock(return_value=client)
    monkeypatch.setattr(version_by_telnet.telnetlib, "Telnet", factory)

    assert version_by_telnet.get_version_by_telnet("openWB DimmModul", "sample-host") == "openWB DimmModul"
    factory.assert_called_once_with("sample-host", 8898, 2)
    client.read_until.assert_called_once_with(bytearray(b"openWB DimmModul"), 2)
    client.__exit__.assert_called_once_with(None, None, None)


@pytest.mark.parametrize("error", [ConnectionRefusedError(), socket.timeout()])
def test_connection_errors_propagate(monkeypatch, error: Exception):
    monkeypatch.setattr(version_by_telnet.telnetlib, "Telnet", Mock(side_effect=error))

    with pytest.raises(type(error)):
        version_by_telnet.get_version_by_telnet("openWB DimmModul", "sample-host")


def test_missing_ip_address_does_not_connect(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(version_by_telnet.telnetlib, "Telnet", factory)

    with pytest.raises(socket.timeout):
        version_by_telnet.get_version_by_telnet("openWB DimmModul", None)
    factory.assert_not_called()
