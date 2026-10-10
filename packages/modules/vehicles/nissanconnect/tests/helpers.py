"""Shared synthetic responses, transport and clocks; no account captures."""
import json
from urllib.parse import parse_qs, urlsplit

from modules.vehicles.nissanconnect.src.api import HttpResponse, NissanClient


# Deliberately invented test values, unrelated to any account or vehicle.
VIN = "SJNFAAZE1U0000001"
SECOND_VIN = "SJNFAAZE1U0000002"
MEASURED_UNIX_SECONDS = 1640995200.0
FORM = ('<form action="/commonauth"><input name="sessionDataKey" value="synthetic-session">'
        '<input name="regionCode" value="EU"><input name="password" type="password"></form>')


def reply(body, status=200, headers=None):
    return HttpResponse(status, headers or {}, body if isinstance(body, str) else json.dumps(body))


def battery(soc=47, timestamp="2022-01-01T00:00:00Z", **extra):
    return {"data": {"attributes": dict(batteryLevel=soc, lastUpdateTime=timestamp, **extra)}}


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.cookies_cleared = 0

    def clear_cookies(self):
        self.cookies_cleared += 1

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        assert self.responses, "Unexpected extra HTTP request"
        response = self.responses.pop(0)
        return response(self.calls) if callable(response) else response


def login_script():
    def authorize(calls):
        state = parse_qs(urlsplit(calls[-2][1]).query)["state"][0]
        return reply("", 302, {"Location": "com://wso2.service.nci?code=synthetic-code&state=" + state})
    return [reply(FORM), authorize, reply({"id_token": "synthetic-id"}),
            reply({"access_token": "synthetic-access", "refresh_token": "synthetic-refresh", "expires_in": 3600})]


def make_client(responses, vin=None):
    transport = ScriptedTransport(responses)
    ticks_monotonic_seconds = [0.0]
    client = NissanClient("synthetic@example.invalid", "synthetic-password", vin, transport,
                          monotonic_seconds=lambda: ticks_monotonic_seconds[0],
                          unix_seconds=lambda: MEASURED_UNIX_SECONDS + 86400)
    return client, transport, ticks_monotonic_seconds


def full_script(vehicles=None):
    return login_script() + [reply({"userId": "synthetic-user"}),
                             reply({"data": [{"vin": VIN}] if vehicles is None else vehicles}),
                             reply(battery(rangeHvacOn=123.4))]
