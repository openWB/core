"""One passive settings test. Credentials arrive on stdin, never in argv or files."""
import json
import logging
import os
import re
import sys

if __package__:
    from .src.api import AuthenticationError, NissanClient, NissanError, RateLimitError, VIN_PATTERN
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.api import AuthenticationError, NissanClient, NissanError, RateLimitError, VIN_PATTERN


# Python validates decoded strings in characters; PHP also limits HTTP bytes.
MAX_STDIN_CHARACTERS = 8192
MAX_USER_ID_CHARACTERS = 320
MAX_PASSWORD_CHARACTERS = 4096
ALLOWED_INPUT_FIELDS = frozenset({"user_id", "password", "vin"})
AGENT_ENVIRONMENT_VARIABLES = ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_CI")


def run_test(payload, client_factory=NissanClient):
    """Validate one unsaved test and return diagnostics or a fixed public error code.

    No MQTT/configuration writes. PHP owns cross-request locking and cooldowns;
    this short-lived worker does not share scheduled-client tokens or backoff.
    """
    if not isinstance(payload, dict) or set(payload) - ALLOWED_INPUT_FIELDS:
        return {"success": False, "code": "invalid_input"}
    user = payload.get("user_id")
    password = payload.get("password")
    vin = payload.get("vin")
    if vin == "":
        vin = None
    if (not isinstance(user, str) or not user.strip() or len(user) > MAX_USER_ID_CHARACTERS
            or not isinstance(password, str) or not password or len(password) > MAX_PASSWORD_CHARACTERS
            or (vin is not None and (not isinstance(vin, str)
                                     or not re.fullmatch(VIN_PATTERN, vin.strip().upper())))):
        return {"success": False, "code": "invalid_input"}
    client = None
    try:
        client = client_factory(user.strip(), password, vin.strip().upper() if vin else None)
        client.fetch_battery(include_odometer=True)
        return {"success": True, "code": "success", "query": client.last_query}
    except AuthenticationError:
        code = "authentication_failed"
    except RateLimitError:
        code = "rate_limited"
    except NissanError:
        code = "query_failed"
    except Exception:
        # Neither exception messages nor tracebacks belong in the web response.
        return {"success": False, "code": "internal_error"}
    return {"success": False, "code": code, "query": client.last_query if client else None}


def main():
    logging.disable(logging.CRITICAL)
    if any(os.environ.get(name) for name in AGENT_ENVIRONMENT_VARIABLES):
        result = {"success": False, "code": "agent_environment"}
    else:
        try:
            body = sys.stdin.read(MAX_STDIN_CHARACTERS + 1)
            result = run_test(json.loads(body)) if len(body) <= MAX_STDIN_CHARACTERS else {
                "success": False, "code": "invalid_input"}
        except Exception:
            result = {"success": False, "code": "invalid_input"}
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
