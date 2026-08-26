import pytest

from helpermodules.logger import redact_sensitive_info


@pytest.mark.parametrize("message, expected", [
    pytest.param("connection to ws://openwb:secret@ocpp.example.com/v16/ established",
                 "connection to ws://openwb:***REDACTED***@ocpp.example.com/v16/ established",
                 id="websocket url"),
    pytest.param("wss://openwb:secret@ocpp.example.com:443/v16/",
                 "wss://openwb:***REDACTED***@ocpp.example.com:443/v16/",
                 id="port is kept"),
    pytest.param('{"url": "ws://openwb:secret@ocpp.example.com/v16/", "version": "1.6"}',
                 '{"url": "ws://openwb:***REDACTED***@ocpp.example.com/v16/", "version": "1.6"}',
                 id="url embedded in json"),
    pytest.param("ws://user:p@ssword@host/",
                 "ws://user:***REDACTED***@host/",
                 id="at sign within password"),
    pytest.param("ws://openwb:***REDACTED***@ocpp.example.com/v16/",
                 "ws://openwb:***REDACTED***@ocpp.example.com/v16/",
                 id="already redacted"),
])
def test_redact_url_credentials(message, expected):
    assert redact_sensitive_info(message) == expected


@pytest.mark.parametrize("message", [
    pytest.param("http://192.168.1.5:8080/api?value=1", id="url without credentials"),
    pytest.param("https://api.example.com/mail?to=someone@example.com", id="at sign in query"),
    pytest.param("http://host:8080 unreachable, contact someone@example.com", id="mail address after url"),
])
def test_keep_url_without_credentials(message):
    assert redact_sensitive_info(message) == message


def test_redact_url_credentials_and_known_field():
    message = '{"url": "ws://openwb:secret@ocpp.example.com/v16/", "password": "abc123"}'
    expected = '{"url": "ws://openwb:***REDACTED***@ocpp.example.com/v16/", "password": "***REDACTED***"}'

    assert redact_sensitive_info(message) == expected


def test_redact_url_credentials_with_sensitive_field_as_user_name():
    # If the user name matches an entry of KNOWN_SENSITIVE_FIELDS, the field pattern applies on
    # top and truncates the url. The password is removed in that case as well.
    assert redact_sensitive_info("ws://token:secret@ocpp.example.com/v16/") == "ws://token=***REDACTED***"
