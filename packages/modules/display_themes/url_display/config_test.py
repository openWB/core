import socket

import pytest

from modules.display_themes import deserialize_display_theme
from modules.display_themes.url_display import config


@pytest.fixture(autouse=True)
def local_networks(monkeypatch):
    def run_command(command):
        assert command == ["ip", "-j", "-4", "address", "show", "up"]
        return '[{"addr_info": [{"family": "inet", "local": "100.64.1.10", "prefixlen": 24}]}]'

    monkeypatch.setattr(
        config,
        "run_command",
        run_command,
    )


def mock_dns(monkeypatch, *addresses):
    def getaddrinfo(host, port, *, family, type):
        assert host
        assert port is None or isinstance(port, int)
        assert family == socket.AF_INET
        assert type == socket.SOCK_STREAM
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 0))
            for address in addresses
        ]

    monkeypatch.setattr(
        config.socket,
        "getaddrinfo",
        getaddrinfo,
    )


@pytest.mark.parametrize("address", [
    "10.0.0.1",
    "172.16.0.1",
    "172.31.255.254",
    "192.168.1.1",
])
def test_rfc1918_address_is_allowed(monkeypatch, address):
    mock_dns(monkeypatch, address)

    assert config.validate_url("https://example.local:8443/path?value=1") == (
        "https://example.local:8443/path?value=1"
    )


def test_rfc1918_validation_does_not_require_interface_lookup(monkeypatch):
    mock_dns(monkeypatch, "192.168.1.10")
    monkeypatch.setattr(
        config,
        "run_command",
        lambda command: pytest.fail(
            f"Interface lookup should not be called for RFC1918 addresses: {command}"
        ),
    )

    assert config.validate_url("openwb.local") == "http://openwb.local"


def test_address_in_local_subnet_is_allowed(monkeypatch):
    mock_dns(monkeypatch, "100.64.1.25")

    assert config.validate_url("evcc.local/status") == "http://evcc.local/status"


@pytest.mark.parametrize("address", [
    "8.8.8.8",
    "100.64.2.25",
    "172.15.255.255",
    "172.32.0.1",
])
def test_non_local_address_is_rejected(monkeypatch, address):
    mock_dns(monkeypatch, address)

    with pytest.raises(ValueError, match="lokalen Netzwerk"):
        config.validate_url("https://example.com")


def test_all_resolved_addresses_must_be_local(monkeypatch):
    mock_dns(monkeypatch, "192.168.1.10", "8.8.8.8")

    with pytest.raises(ValueError, match="8.8.8.8"):
        config.validate_url("https://example.local")


@pytest.mark.parametrize("url", [
    "",
    "ftp://192.168.1.10",
    "http://user:password@192.168.1.10",
    "http://192.168.1.10:invalid",
])
def test_invalid_url_is_rejected(monkeypatch, url):
    mock_dns(monkeypatch, "192.168.1.10")

    with pytest.raises(ValueError):
        config.validate_url(url)


def test_unresolvable_hostname_is_rejected(monkeypatch):
    def raise_gaierror(*args, **kwargs):
        assert args or kwargs
        raise socket.gaierror

    monkeypatch.setattr(config.socket, "getaddrinfo", raise_gaierror)

    with pytest.raises(ValueError, match="konnte nicht aufgelöst werden"):
        config.validate_url("https://missing.local")


@pytest.mark.parametrize("configuration", [None, "https://192.168.1.10", 1, []])
def test_non_object_theme_configuration_is_rejected(configuration):
    with pytest.raises(ValueError, match="JSON-Objekt"):
        deserialize_display_theme({
            "name": "URL Display",
            "type": "url_display",
            "configuration": configuration,
        })


@pytest.mark.parametrize("theme_type", ["cards", "colors", "url_display"])
def test_display_theme_configuration_is_deserialized(theme_type):
    theme = deserialize_display_theme({
        "type": theme_type,
        "configuration": {},
    })

    assert theme.type == theme_type
    assert not isinstance(theme.configuration, dict)
