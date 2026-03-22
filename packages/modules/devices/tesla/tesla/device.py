#!/usr/bin/env python3
import logging
import requests
from requests import HTTPError
from typing import Iterable, Union, Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.req import get_http_session
from modules.devices.tesla.tesla.bat import TeslaBat
from modules.devices.tesla.tesla.config import Tesla, TeslaBatSetup, TeslaCounterSetup, TeslaInverterSetup
from modules.devices.tesla.tesla.counter import TeslaCounter
from modules.devices.tesla.tesla.http_client import PowerwallHttpClient
from modules.devices.tesla.tesla.inverter import TeslaInverter

log = logging.getLogger(__name__)


def __update_components(client: PowerwallHttpClient,
                        components: Iterable[Union[TeslaBat, TeslaCounter, TeslaInverter]]):
    """Update all Powerwall components.

    Fail-fast: if any request inside a component update fails, abort the remaining
    component updates for this cycle to avoid stressing the gateway during reboot.
    """
    aggregate = client.get_json("/api/meters/aggregates")
    for component in components:
        with SingleComponentUpdateContext(component.fault_state):
            component.update(client, aggregate)
        # If a request failed inside the component update but was swallowed by the
        # component context, the HTTP client will still mark the cycle as failed.
        if getattr(client, "cycle_failed", False):
            device_ip = getattr(client, "_PowerwallHttpClient__host", "")
            conn_stats = _get_conn_state_counts_proc(device_ip, 443)
            log.warning(
                "Powerwall FAIL-FAST: aborting remaining component updates for this cycle (device_ip=%s) conn-stats=%s",
                device_ip,
                conn_stats if conn_stats else "{}",
            )
            break


def _authenticate(session: requests.Session, url: str, email: str, password: str):
    """
    email is not yet required for login (2022/01), but we simulate the whole login page
    """
    response = session.post(
        "https://" + url + "/api/login/Basic",
        json={"username": "customer", "email": email, "password": password, "force_sm_off": False},
        verify=False,
        timeout=5
    )
    response.raise_for_status()

    # Do NOT log cookie values (secrets). Only log cookie names.
    try:
        cookie_names = [c.name for c in response.cookies]
    except Exception:
        cookie_names = []
    log.debug("Powerwall login ok, cookies set: %s", cookie_names)

    return {"AuthCookie": response.cookies["AuthCookie"], "UserRecord": response.cookies["UserRecord"]}


def _get_conn_state_counts_proc(dst_ip: str, dst_port: int = 443) -> dict:
    """Native alternative to `ss`: counts TCP connection states via /proc/net/tcp(+6)."""
    # State codes from linux tcp_states:
    state_map = {
        "01": "ESTABLISHED",
        "02": "SYN_SENT",
        "03": "SYN_RECV",
        "04": "FIN_WAIT1",
        "05": "FIN_WAIT2",
        "06": "TIME_WAIT",
        "07": "CLOSE",
        "08": "CLOSE_WAIT",
        "09": "LAST_ACK",
        "0A": "LISTEN",
        "0B": "CLOSING",
    }

    def ip_to_hex(ip: str) -> str:
        # /proc/net/tcp stores IPv4 in little-endian hex
        parts = ip.split(".")
        if len(parts) != 4:
            return ""
        return "".join(f"{int(o):02X}" for o in reversed(parts))

    target_ip_hex = ip_to_hex(dst_ip)
    target_port_hex = f"{dst_port:04X}"
    if not target_ip_hex:
        return {}

    counts = {}

    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                next(f, None)  # header
                for line in f:
                    parts = line.split()
                    if len(parts) < 4:
                        continue
                    remote = parts[2]  # rem_address
                    state = parts[3]
                    r_ip, r_port = remote.split(":")
                    if r_ip == target_ip_hex and r_port == target_port_hex:
                        name = state_map.get(state, state)
                        counts[name] = counts.get(name, 0) + 1
        except FileNotFoundError:
            continue
        except Exception:
            # best-effort: if proc parsing fails, just return what we have
            continue

    return counts


def create_device(device_config: Tesla):
    http_client = None
    session: Optional[requests.Session] = None
    last_session_id: Optional[int] = None
    update_counter = 0

    def create_bat_component(component_config: TeslaBatSetup):
        return TeslaBat(component_config)

    def create_counter_component(component_config: TeslaCounterSetup):
        return TeslaCounter(component_config)

    def create_inverter_component(component_config: TeslaInverterSetup):
        return TeslaInverter(component_config)

    def update_components(components: Iterable[Union[TeslaBat, TeslaCounter, TeslaInverter]]):
        """
        This is called repeatedly by openWB. We log the session id to verify
        whether openWB keeps the same requests.Session across polling cycles.
        """
        nonlocal http_client, session, last_session_id, update_counter
        update_counter += 1

        address = device_config.configuration.ip_address
        email = device_config.configuration.email
        password = device_config.configuration.password

        current_session_id = id(session) if session is not None else None

        # Log session reuse occasionally (every 60 cycles) and whenever it changes.
        if current_session_id != last_session_id:
            log.info(
                "Powerwall session changed device_ip=%s old_session_id=%s new_session_id=%s update_counter=%s",
                address, last_session_id, current_session_id, update_counter
            )
            last_session_id = current_session_id
        elif update_counter % 60 == 0:
            log.info(
                "Powerwall session ok device_ip=%s session_id=%s update_counter=%s",
                address, current_session_id, update_counter
            )
            conn_stats = _get_conn_state_counts_proc(address, 443)
            if conn_stats:
                log.info("Powerwall conn-stats device_ip=%s update_counter=%s %s", address, update_counter, conn_stats)

        log.debug("Beginning update (device_ip=%s update_counter=%s)", address, update_counter)

        # reset fail-fast flag for this polling cycle
        if hasattr(http_client, "reset_cycle"):
            http_client.reset_cycle()

        # First run after process start: no cookies -> authenticate once
        if http_client.cookies is None:
            http_client.cookies = _authenticate(session, address, email, password)
            http_client.mark_cookie_renewed()
            __update_components(http_client, components)
            return

        # Normal operation: reuse cookie. If it fails with 401/403 -> re-auth
        try:
            __update_components(http_client, components)
            return
        except HTTPError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status != 401 and status != 403:
                raise e
            log.warning(
                "Login to powerwall with existing cookie failed (status=%s). Will retry with new cookie...",
                status
            )

        http_client.cookies = _authenticate(session, address, email, password)

        http_client.mark_cookie_renewed()
        __update_components(http_client, components)
        log.debug("Update completed successfully (device_ip=%s update_counter=%s)", address, update_counter)

    def initializer():
        """
        Called when openWB instantiates the device. If this happens frequently,
        you'll see session_id changes (and more TLS handshakes).
        """
        nonlocal http_client, session, last_session_id, update_counter
        update_counter = 0
        session = get_http_session()
        http_client = PowerwallHttpClient(device_config.configuration.ip_address, session, None)

        last_session_id = id(session)
        log.info(
            "Powerwall device initialized device_ip=%s session_id=%s http_client_id=%s",
            device_config.configuration.ip_address, last_session_id, id(http_client)
        )

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Tesla)

