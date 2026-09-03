import ipaddress
import json
import socket
import subprocess
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from helpermodules.auto_str import auto_str
from helpermodules.utils.run_command import run_command

from modules.common.abstract_device import DeviceDescriptor


RFC1918_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)


def _get_local_ipv4_networks() -> tuple[ipaddress.IPv4Network, ...]:
    try:
        output = run_command(["ip", "-j", "-4", "address", "show", "up"])
        if output is None:
            raise ValueError("Der Aufruf von 'ip' hat keine Ausgabe geliefert.")
        interfaces = json.loads(output)
        return tuple(
            ipaddress.IPv4Network(f"{address['local']}/{address['prefixlen']}", strict=False)
            for interface in interfaces
            for address in interface.get("addr_info", [])
            if address.get("family") == "inet"
        )
    except (KeyError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        raise ValueError("Die lokalen IPv4-Netzwerke konnten nicht ermittelt werden.") from exc


def validate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Bitte eine URL angeben.")

    normalized_url = url.strip()
    if "://" not in normalized_url:
        normalized_url = f"http://{normalized_url}"

    parsed_url = urlsplit(normalized_url)
    if parsed_url.scheme.lower() not in ("http", "https"):
        raise ValueError("Die URL muss das Protokoll HTTP oder HTTPS verwenden.")
    if parsed_url.hostname is None:
        raise ValueError("Die URL enthält keinen gültigen Hostnamen.")
    if parsed_url.username is not None or parsed_url.password is not None:
        raise ValueError("Die URL darf keine Zugangsdaten enthalten.")
    try:
        parsed_url.port
    except ValueError as exc:
        raise ValueError("Die URL enthält keinen gültigen Port.") from exc

    try:
        resolved_addresses = {
            ipaddress.IPv4Address(address[4][0])
            for address in socket.getaddrinfo(
                parsed_url.hostname,
                parsed_url.port,
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ValueError(f"Der Hostname '{parsed_url.hostname}' konnte nicht aufgelöst werden.") from exc

    if not resolved_addresses:
        raise ValueError(f"Für den Hostnamen '{parsed_url.hostname}' wurde keine IPv4-Adresse gefunden.")

    addresses_outside_rfc1918 = [
        address
        for address in resolved_addresses
        if not any(address in network for network in RFC1918_NETWORKS)
    ]
    if not addresses_outside_rfc1918:
        return urlunsplit(parsed_url._replace(scheme=parsed_url.scheme.lower()))

    local_networks = _get_local_ipv4_networks()
    invalid_addresses = [
        str(address)
        for address in addresses_outside_rfc1918
        if not any(address in network for network in local_networks)
    ]
    if invalid_addresses:
        raise ValueError(
            "Die URL muss auf eine IPv4-Adresse im lokalen Netzwerk zeigen. "
            f"Nicht zulässig: {', '.join(sorted(invalid_addresses))}"
        )

    return urlunsplit(parsed_url._replace(scheme=parsed_url.scheme.lower()))


@auto_str
class UrlDisplayThemeConfiguration:
    def __init__(self,
                 url: str = ""
                 ) -> None:
        self.url = validate_url(url) if url else ""


@auto_str
class UrlDisplayTheme:
    def __init__(self,
                 name: str = "URL Display",
                 type: str = "url_display",
                 official: bool = False,
                 userManagementSupported: bool = False,
                 configuration: Optional[UrlDisplayThemeConfiguration] = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.userManagementSupported = userManagementSupported
        self.configuration = configuration or UrlDisplayThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=UrlDisplayTheme)
