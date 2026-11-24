"""Four-tier authentication for the simpleAPI HTTP server.

Precedence: bearer token, local username/password, bare token parameter, then the MQTT broker itself
(credentials are validated against the public listener, see broker_access). Tokens and local users from the
config are trusted; broker users stay subject to the broker's ACLs.
"""
import hmac
import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from passlib.hash import bcrypt

from .broker_access import Principal, TRUSTED

log = logging.getLogger("simpleAPI")


@dataclass
class AuthConfig:
    enabled: bool = True
    require_https: bool = False
    tokens: List[str] = field(default_factory=list)
    users: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "AuthConfig":
        return cls(
            enabled=data.get('enabled', True),
            require_https=data.get('require_https', False),
            tokens=list(data.get('tokens', [])),
            users=dict(data.get('users', {})),
        )


class Authenticator:
    def __init__(self, config: AuthConfig, credential_tester: Callable[[str, str], bool]):
        self.config = config
        self._credential_tester = credential_tester

    def authenticate(self, params: Dict[str, str], bearer_token: Optional[str], is_https: bool) -> Optional[Principal]:
        """Returns who is calling, or None if the request is not authenticated."""
        if not self.config.enabled:
            return TRUSTED

        if bearer_token and self._validate_token(bearer_token):
            return TRUSTED

        secure_enough = is_https or not self.config.require_https
        username = params.get('username')
        password = params.get('password')
        if username is not None and password is not None:
            if not secure_enough:
                return None
            # supplied credentials are never silently downgraded to anonymous access
            return self._validate_credentials(username, password)

        token = params.get('token')
        if token is not None and secure_enough and self._validate_token(token):
            return TRUSTED

        # no usable credentials: whatever the broker grants an anonymous client
        return Principal() if self._credential_tester('', '') else None

    def _validate_token(self, token: str) -> bool:
        return any(hmac.compare_digest(valid, token) for valid in self.config.tokens)

    def _validate_credentials(self, username: str, password: str) -> Optional[Principal]:
        users = self.config.users
        if users and username in users:
            stored = users[username]
            if stored.startswith('$'):
                try:
                    valid = bcrypt.verify(password, stored)
                except ValueError:
                    valid = False
            else:
                valid = hmac.compare_digest(stored, password)
            return TRUSTED if valid else None
        return Principal(username=username, password=password) if self._credential_tester(username, password) else None
