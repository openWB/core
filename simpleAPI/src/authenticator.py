"""Four-tier authentication for the simpleAPI HTTP server.

Precedence: bearer token, local username/password, bare token parameter,
then a fallback that delegates to the MQTT broker itself - if the broker
accepts anonymous connections, simpleAPI is effectively open too.
"""
import hmac
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import paho.mqtt.client as mqtt
from passlib.hash import bcrypt

log = logging.getLogger("simpleAPI")


@dataclass
class AuthConfig:
    enabled: bool = False
    require_https: bool = False
    tokens: List[str] = field(default_factory=list)
    users: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "AuthConfig":
        return cls(
            enabled=data.get('enabled', False),
            require_https=data.get('require_https', False),
            tokens=list(data.get('tokens', [])),
            users=dict(data.get('users', {})),
        )


def test_mqtt_credentials(
        host: str, port: int, use_tls: bool, validate_cert: bool,
        username: str, password: str, timeout: float = 3.0) -> bool:
    """Probe the broker with a short-lived connection instead of shelling out to
    mosquitto_sub. An empty username/password tests anonymous access."""
    outcome: Dict[str, Optional[int]] = {'rc': None}

    def on_connect(client, userdata, flags, rc):
        outcome['rc'] = rc

    client = mqtt.Client()
    client.on_connect = on_connect
    if use_tls:
        client.tls_set(cert_reqs=__import__('ssl').CERT_REQUIRED)
        if not validate_cert:
            client.tls_insecure_set(True)
    if username:
        client.username_pw_set(username, password)

    try:
        client.connect(host, port, keepalive=max(int(timeout), 1))
    except Exception as exc:
        log.debug(f"MQTT credential probe failed to connect: {exc}")
        return False

    client.loop_start()
    deadline = time.monotonic() + timeout
    try:
        while outcome['rc'] is None and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass

    return outcome['rc'] == 0


class Authenticator:
    def __init__(self, config: AuthConfig, mqtt_params: Dict,
                 credential_tester: Callable[..., bool] = test_mqtt_credentials):
        self.config = config
        self.mqtt_params = mqtt_params
        self._credential_tester = credential_tester

    def authenticate(self, params: Dict[str, str], bearer_token: Optional[str], is_https: bool) -> bool:
        if not self.config.enabled:
            return True

        if bearer_token and self._validate_token(bearer_token):
            return True

        username = params.get('username')
        password = params.get('password')
        if username is not None and password is not None:
            if (is_https or not self.config.require_https) and self._validate_credentials(username, password):
                return True

        token = params.get('token')
        if token is not None:
            if (is_https or not self.config.require_https) and self._validate_token(token):
                return True

        return self._test_broker_anonymous()

    def _validate_token(self, token: str) -> bool:
        return any(hmac.compare_digest(valid, token) for valid in self.config.tokens)

    def _validate_credentials(self, username: str, password: str) -> bool:
        users = self.config.users
        if users and username in users:
            stored = users[username]
            if stored.startswith('$'):
                try:
                    return bcrypt.verify(password, stored)
                except ValueError:
                    return False
            return hmac.compare_digest(stored, password)
        return self._credential_tester(username=username, password=password, **self.mqtt_params)

    def _test_broker_anonymous(self) -> bool:
        return self._credential_tester(username='', password='', **self.mqtt_params)
