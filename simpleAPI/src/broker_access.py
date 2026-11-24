"""Per-user broker permissions for the simpleAPI HTTP server.

The old PHP implementation ran every read and write with the caller's own MQTT credentials against the
public broker listener, so Mosquitto's ACLs (dynamic security with user management) decided what a caller could
see or change. The daemon itself uses one local, unrestricted connection and serves reads from its cache, so
those permissions have to be re-checked against the public listener with the caller's credentials:

- login: the credentials must be accepted by the broker (CONNACK).
- read: dynsec allows SUBSCRIBE by default and filters at delivery (publishClientReceive), so a SUBACK says
  nothing. The retained messages of the topics a request reads must actually be delivered to the caller.
- write: the publish is done through the caller's own MQTT 5 connection and the PUBACK reason code is checked.
"""
import hashlib
import logging
import ssl
import struct
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

import paho.mqtt.client as mqtt

log = logging.getLogger("simpleAPI")

PUBACK_FAILURE = 0x80


@dataclass(frozen=True)
class Principal:
    """Who is calling. `trusted` principals (local token/user from the config) are not subject to broker ACLs."""
    trusted: bool = False
    username: str = ''
    password: str = ''

    def cache_key(self) -> str:
        # includes the password so a wrong password can never reuse the cached result of a correct one
        return hashlib.sha256(f"{self.username}\0{self.password}".encode('utf-8')).hexdigest()


TRUSTED = Principal(trusted=True)


class _AckClient(mqtt.Client):
    """paho 1.6.1 does not hand the PUBACK reason code of an MQTT 5 publish to any callback."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puback_reasons: Dict[int, int] = {}

    def _handle_pubackcomp(self, cmd):
        packet = self._in_packet.get('packet') or b''
        if cmd == 'PUBACK' and self._protocol == mqtt.MQTTv5 and len(packet) >= 2:
            mid, = struct.unpack("!H", packet[:2])
            self.puback_reasons[mid] = packet[2] if len(packet) > 2 else 0
        return super()._handle_pubackcomp(cmd)


class UserSession:
    """MQTT 5 connection with the caller's credentials; every publish raises PermissionError if refused."""

    def __init__(self, client: _AckClient, timeout: float):
        self._client = client
        self._timeout = timeout

    def publish(self, topic: str, payload, retain: bool = True) -> None:
        info = self._client.publish(topic, payload, qos=1, retain=retain)
        info.wait_for_publish(timeout=self._timeout)
        if not info.is_published():
            raise TimeoutError(f"Publish to {topic} was not acknowledged by the broker")
        if self._client.puback_reasons.pop(info.mid, 0) >= PUBACK_FAILURE:
            raise PermissionError(f"Not authorized to publish to {topic}")

    def close(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()


class BrokerAccess:
    def __init__(self, host: str = 'localhost', port: int = 8883, use_tls: bool = True,
                 validate_cert: bool = False, timeout: float = 3.0, read_timeout: float = 1.5,
                 cache_ttl: float = 30.0,
                 client_factory: Callable[..., _AckClient] = _AckClient):
        self.host = host
        self.port = port
        self.use_tls = use_tls
        self.validate_cert = validate_cert
        self.timeout = timeout
        # retained messages arrive right after the subscription; a topic that has not shown up by then is denied
        self.read_timeout = read_timeout
        self.cache_ttl = cache_ttl
        self._client_factory = client_factory
        self._read_cache: Dict[Tuple[str, frozenset], Tuple[float, Tuple[str, ...]]] = {}
        self._login_cache: Dict[str, float] = {}
        self._cache_lock = threading.Lock()

    @classmethod
    def from_config(cls, config: Dict) -> "BrokerAccess":
        return cls(
            host=config.get('host', 'localhost'),
            port=config.get('port', 8883),
            use_tls=config.get('use_tls', True),
            validate_cert=config.get('validate_cert', False),
        )

    def _connect(self, protocol: int, principal: Principal) -> Tuple[_AckClient, threading.Event, List[int]]:
        connected = threading.Event()
        result: List[int] = []

        def on_connect(client, userdata, flags, rc, properties=None):
            result.append(getattr(rc, 'value', rc))
            connected.set()

        client = self._client_factory(protocol=protocol)
        client.on_connect = on_connect
        if self.use_tls:
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED if self.validate_cert else ssl.CERT_NONE)
            if not self.validate_cert:
                client.tls_insecure_set(True)
        if principal.username:
            client.username_pw_set(principal.username, principal.password)
        client.connect(self.host, self.port, keepalive=30)
        client.loop_start()
        return client, connected, result

    def _open(self, protocol: int, principal: Principal) -> Optional[_AckClient]:
        try:
            client, connected, result = self._connect(protocol, principal)
        except Exception as exc:
            log.debug(f"Broker connection failed: {exc}")
            return None
        if connected.wait(self.timeout) and result and result[-1] == 0:
            return client
        client.disconnect()
        client.loop_stop()
        return None

    def check_credentials(self, username: str, password: str) -> bool:
        """True if the broker accepts the login (an empty username tests anonymous access)."""
        principal = Principal(username=username, password=password)
        key = principal.cache_key()
        now = time.monotonic()
        with self._cache_lock:
            if self._login_cache.get(key, 0.0) > now:
                return True
        client = self._open(mqtt.MQTTv311, principal)
        if client is None:
            return False
        client.disconnect()
        client.loop_stop()
        with self._cache_lock:
            self._login_cache = {k: v for k, v in self._login_cache.items() if v > now}
            self._login_cache[key] = now + self.cache_ttl
        return True

    def denied_topics(self, principal: Principal, topics: Iterable[str]) -> List[str]:
        """Topics whose retained value the principal does not receive from the broker."""
        wanted = frozenset(topics)
        if not wanted:
            return []
        key = (principal.cache_key(), wanted)
        now = time.monotonic()
        with self._cache_lock:
            cached = self._read_cache.get(key)
            if cached and cached[0] > now:
                return list(cached[1])

        denied = self._probe_read(principal, wanted)

        with self._cache_lock:
            self._read_cache = {k: v for k, v in self._read_cache.items() if v[0] > now}
            self._read_cache[key] = (now + self.cache_ttl, tuple(denied))
        return denied

    def _probe_read(self, principal: Principal, wanted: Set[str]) -> List[str]:
        received: Set[str] = set()
        done = threading.Event()

        try:
            client, connected, result = self._connect(mqtt.MQTTv311, principal)
        except Exception as exc:
            log.debug(f"Broker connection failed: {exc}")
            return sorted(wanted)

        def on_message(client, userdata, message):
            if message.topic in wanted:
                received.add(message.topic)
                if received >= wanted:
                    done.set()

        client.on_message = on_message
        try:
            if not connected.wait(self.timeout) or not result or result[-1] != 0:
                return sorted(wanted)
            topic_list = sorted(wanted)
            for start in range(0, len(topic_list), 100):
                client.subscribe([(topic, 0) for topic in topic_list[start:start + 100]])
            done.wait(self.read_timeout)
            return sorted(wanted - received)
        finally:
            client.disconnect()
            client.loop_stop()

    def open_session(self, principal: Principal) -> UserSession:
        client = self._open(mqtt.MQTTv5, principal)
        if client is None:
            raise PermissionError("Login to the MQTT broker failed")
        return UserSession(client, self.timeout)
