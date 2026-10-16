"""Synthetic protocol tests; unmatched requests cannot reach Nissan."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging
import re
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
import requests_mock
from urllib3.connectionpool import HTTPSConnectionPool
from urllib3.response import HTTPResponse
from urllib3.util.retry import Retry

from modules.vehicles.nissanconnect import api
from modules.vehicles.nissanconnect.config import NissanConnect, NissanConnectConfiguration

VIN = "SJNFAAZE1U0000001"
OTHER_VIN = "SJNFAAZE1U0000002"
MEASUREMENT_UNIX_SECONDS = 1640995200.0
BATTERY_URL = api.CARS_BASE_URL + "v1/cars/" + VIN + "/battery-status"
COCKPIT_URL = api.CARS_BASE_URL + "v1/cars/" + VIN + "/cockpit"
REFRESH_URL = api.BFF_BASE_URL + "v1/oauth2/refresh-token?platform=Android"
FORM = ('<form action="/commonauth"><input name="sessionDataKey" value="synthetic-session">'
        '<input name="regionCode" value="EU"><input name="password" type="password"></form>')


@pytest.fixture(autouse=True)
def http():
    with requests_mock.Mocker() as mock:
        yield mock


def battery(soc=47, timestamp="2022-01-01T00:00:00Z", **extra):
    return {"data": {"attributes": dict(batteryLevel=soc, lastUpdateTime=timestamp, **extra)}}


def client():
    result = api.NissanClient("synthetic@example.invalid", "synthetic-password")
    result._vin = VIN
    result._install_token({"access_token": "synthetic-access", "refresh_token": "synthetic-refresh"})
    return result


def login(http):
    http.get(re.compile(re.escape(api.AUTH_BASE_URL + "oauth2/authorize?")), text=FORM)

    def callback(request, context):
        state = parse_qs(urlsplit(http.request_history[-2].url).query)["state"][0]
        context.headers["Location"] = api.OAUTH_CALLBACK_URI + "?code=synthetic-code&state=" + state
        return ""

    http.post(api.AUTH_BASE_URL + "commonauth", status_code=302, text=callback)
    http.post(api.AUTH_BASE_URL + "oauth2/token", json={"id_token": "synthetic-id"})
    http.post(api.BFF_BASE_URL + "v1/oauth2/access_token?platform=Android",
              json={"access_token": "synthetic-access", "refresh_token": "synthetic-refresh"})


def test_login_selection_measurements_and_session_reuse(http, caplog):
    caplog.set_level(logging.DEBUG)
    login(http)
    http.get(api.USERS_BASE_URL + "v1/users/current", json={"userId": "synthetic-user"})
    http.get(api.BFF_BASE_URL + "v5/users/synthetic-user/cars", json={"data": [{"vin": VIN}]})
    http.get(BATTERY_URL, json=battery(rangeHvacOn=123.4))
    http.get(COCKPIT_URL, json={"data": {"attributes": {"totalMileage": 12345.6}}})
    instance = api.NissanClient("synthetic@example.invalid", "synthetic-password")
    assert instance.fetch_battery() == (47, 123.4, MEASUREMENT_UNIX_SECONDS, 12345.6)
    calls = list(http.request_history)
    authorize = parse_qs(urlsplit(calls[0].url).query)
    verifier = parse_qs(calls[2].text)["code_verifier"][0]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert authorize["code_challenge"] == [challenge]
    assert parse_qs(calls[1].text)["username"] == ["EU/synthetic@example.invalid"]
    assert calls[3].headers["Authorization"] == "synthetic-id"
    assert calls[-1].headers["Authorization"] == "Bearer synthetic-access"
    assert all(call.timeout == api.REQUEST_TIMEOUT_SECONDS for call in calls)
    assert all("/actions/" not in call.url for call in calls)
    assert not any(record.name == "modules.common.req" for record in caplog.records)
    instance.fetch_battery()
    assert len(http.request_history) == len(calls) + 2


@pytest.mark.parametrize("soc", [0, 47.5, 100])
def test_valid_zero_and_old_measurement(soc):
    assert api.parse_battery(battery(soc, rangeHvacOn=0)) == (soc, 0, MEASUREMENT_UNIX_SECONDS)


@pytest.mark.parametrize("soc", [None, True, -1, 101, "47", float("nan"), float("inf")])
def test_invalid_soc_never_becomes_zero(soc):
    with pytest.raises(api.NissanError):
        api.parse_battery(battery(soc))


@pytest.mark.parametrize("timestamp", [None, "bad", "2022-01-01T00:00:00", "2099-01-01T00:00:00Z"])
def test_invalid_timestamp_never_becomes_now(timestamp):
    with pytest.raises(api.NissanError):
        api.parse_battery(battery(timestamp=timestamp))


@pytest.mark.parametrize("odometer", [None, -1, True, "12345", float("inf")])
def test_unavailable_optional_data_preserves_soc(http, odometer):
    http.get(BATTERY_URL, json=battery(rangeHvacOn=-1))
    http.get(COCKPIT_URL, json={"data": {"attributes": {"totalMileage": odometer}}})
    assert client().fetch_battery() == (47, None, MEASUREMENT_UNIX_SECONDS, None)


def test_optional_endpoint_failure_preserves_soc(http):
    http.get(BATTERY_URL, json=battery(rangeHvacOff=150))
    http.get(COCKPIT_URL, status_code=503)
    assert client().fetch_battery() == (47, 150, MEASUREMENT_UNIX_SECONDS, None)


@pytest.mark.parametrize("status", [429, 503])
def test_service_errors_raise_and_next_core_update_can_retry(http, status):
    http.get(BATTERY_URL, [{"status_code": status, "text": "synthetic-private-body"}, {"json": battery()}])
    http.get(COCKPIT_URL, json={"data": {"attributes": {"totalMileage": 0}}})
    instance = client()
    with pytest.raises(api.NissanError, match=f"HTTP {status}"):
        instance.fetch_battery()
    assert http.call_count == 1
    assert instance.fetch_battery()[-1] == 0


@pytest.mark.parametrize("expired", [False, True])
def test_authentication_refreshes_once(http, expired):
    http.get(BATTERY_URL, [{"json": battery()}] if expired else [{"status_code": 401}, {"json": battery()}])
    http.get(COCKPIT_URL, json={})
    refresh = http.post(REFRESH_URL, json={"access_token": "synthetic-new"})
    instance = client()
    if expired:
        instance._expires_at_monotonic_seconds = 0
    assert instance.fetch_battery()[0] == 47
    assert refresh.call_count == 1
    assert http.last_request.headers["Authorization"] == "Bearer synthetic-new"


def test_rejected_refresh_uses_login_and_repeated_401_stops(http):
    login(http)
    http.get(BATTERY_URL, status_code=401)
    refresh = http.post(REFRESH_URL, status_code=400)
    with pytest.raises(api.AuthenticationError):
        client().fetch_battery()
    assert refresh.call_count == 1
    assert sum(request.url == BATTERY_URL for request in http.request_history) == 2


@pytest.mark.parametrize("target", [
    "https://example.invalid/steal", "http://login.mynissan-account.com/",
    "https://user@login.mynissan-account.com/", "https://login.mynissan-account.com:444/"])
@pytest.mark.parametrize("form", [False, True])
def test_rejects_unsafe_login_destinations(http, target, form):
    http.get(re.compile(re.escape(api.AUTH_BASE_URL)),
             text=FORM.replace("/commonauth", target) if form else "", status_code=200 if form else 302,
             headers={} if form else {"Location": target})
    with pytest.raises(api.NissanError, match="destination"):
        api.NissanClient("synthetic@example.invalid", "synthetic-password").fetch_battery()
    assert http.call_count == 1


def test_oauth_state_mismatch_stops_before_token_exchange(http):
    login(http)
    http.post(api.AUTH_BASE_URL + "commonauth", status_code=302,
              headers={"Location": api.OAUTH_CALLBACK_URI + "?code=synthetic-code&state=wrong"})
    with pytest.raises(api.AuthenticationError):
        api.NissanClient("synthetic@example.invalid", "synthetic-password").fetch_battery()
    assert http.call_count == 2


@pytest.mark.parametrize("configured_vin,vehicles,expected", [
    ("", [VIN, OTHER_VIN], None), (OTHER_VIN, [VIN], None), ("", [], None),
    (OTHER_VIN.lower(), [VIN, OTHER_VIN], OTHER_VIN), ("", [VIN], VIN)])
def test_vehicle_selection(http, configured_vin, vehicles, expected):
    http.get(api.USERS_BASE_URL + "v1/users/current", json={"userId": "synthetic-user"})
    http.get(api.BFF_BASE_URL + "v5/users/synthetic-user/cars", json={"data": [{"vin": vin} for vin in vehicles]})
    instance = client()
    instance._configured_vin = configured_vin.upper()
    if expected:
        instance._select_vehicle()
        assert instance._vin == expected
    else:
        with pytest.raises(api.NissanError):
            instance._select_vehicle()


def test_transport_and_json_errors_omit_private_data(http):
    http.get(BATTERY_URL, exc=requests.Timeout("synthetic-private-url"))
    instance = client()
    with pytest.raises(api.NissanError, match="^Nissan could not be reached.$"):
        instance.fetch_battery()
    http.get(BATTERY_URL, text="synthetic-private-body")
    with pytest.raises(api.NissanError, match="^Nissan returned an invalid response.$"):
        instance.fetch_battery()


def test_native_configuration_roundtrip_and_private_repr():
    from dataclass_utils import asdict, dataclass_from_dict

    config = NissanConnect(configuration=NissanConnectConfiguration("synthetic@example.invalid", "synthetic-password"))
    decoded = dataclass_from_dict(NissanConnect, asdict(config))
    assert decoded == config
    assert "synthetic" not in repr(config)
    assert NissanConnect().configuration is not NissanConnect().configuration


@pytest.mark.parametrize("path", [
    "/car-adapter/v1/cars/" + VIN + "/battery-status",
    "/bff-web/v5/users/synthetic-user/cars",
    "/commonauth?code=synthetic-code&sessionDataKey=synthetic-session",
])
@pytest.mark.parametrize("fail", [False, True])
def test_transport_logs_hide_private_urls_without_muting_other_requests(monkeypatch, caplog, path, fail):
    caplog.set_level(logging.DEBUG)
    instance = client()
    pool = HTTPSConnectionPool("example.invalid")
    connection = Mock(is_closed=False, is_verified=True)
    connection.getresponse.return_value = HTTPResponse(status=200, headers={}, preload_content=False)
    monkeypatch.setattr(pool, "_validate_conn", lambda connection: None)
    transport_log = logging.getLogger("urllib3.connectionpool")

    def request(*args, **kwargs):
        # Real urllib3 log paths, but a fake connection: no socket or Nissan access.
        pool._make_request(connection, "GET", path)
        Retry(total=1).increment("GET", path)
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(transport_log.debug, "Other vehicle request remains visible").result()
        api.log.debug("Nissan diagnostic remains visible")
        if fail:
            raise requests.Timeout("synthetic-private-url")
        return Mock(status_code=200)

    monkeypatch.setattr(instance._session, "request", request)
    if fail:
        with pytest.raises(api.NissanError, match="^Nissan could not be reached.$"):
            instance._request("GET", "https://example.invalid" + path)
    else:
        assert instance._request("GET", "https://example.invalid" + path).status_code == 200
    transport_log.debug("Subsequent request remains visible")
    assert path not in caplog.text
    assert "synthetic-private-url" not in caplog.text
    assert "Other vehicle request remains visible" in caplog.text
    assert "Nissan diagnostic remains visible" in caplog.text
    assert "Subsequent request remains visible" in caplog.text
