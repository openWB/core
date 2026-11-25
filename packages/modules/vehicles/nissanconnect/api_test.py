"""Synthetic protocol tests; unmatched requests cannot reach Nissan."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.client import HTTPMessage, RemoteDisconnected
from importlib import import_module
import logging
import re
from socket import gaierror
import traceback
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
import requests_mock
from urllib3.connectionpool import HTTPSConnectionPool
from urllib3.exceptions import MaxRetryError, NewConnectionError, ProtocolError
from urllib3.response import HTTPResponse
from urllib3.util.retry import Retry

from modules.vehicles.nissanconnect import api
from modules.vehicles.nissanconnect.config import NissanConnect, NissanConnectConfiguration

VIN = "SJNFAAZE1U0000001"
OTHER_VIN = "SJNFAAZE1U0000002"
MEASUREMENT_UNIX_SECONDS = 1640995200.0
BATTERY_URL = api.CARS_BASE_URL + "v1/cars/" + VIN + "/battery-status"
COCKPIT_URL = api.CARS_BASE_URL + "v1/cars/" + VIN + "/cockpit"
ACTIVE_REFRESH_URL = api.CARS_BASE_URL + "v1/cars/" + VIN + "/actions/refresh-battery-status"
ACTION_STATUS_URL = api.CARS_BASE_URL + "v1/cars/" + VIN + "/actions/status?actionId=synthetic-action"
REFRESH_URL = api.BFF_BASE_URL + "v1/oauth2/refresh-token?platform=Android"
FORM = ('<form action="/commonauth"><input name="sessionDataKey" value="synthetic-session">'
        '<input name="regionCode" value="EU"><input name="password" type="password"></form>')


@pytest.fixture(autouse=True)
def http(caplog):
    # Mock request URLs are test infrastructure; keep real HTTP and module logs checked.
    caplog.set_level(logging.WARNING, logger="requests_mock.adapter")
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
    http.get(BATTERY_URL, json=battery(batteryBarLevel=114, rangeHvacOn=123.4))
    http.get(COCKPIT_URL, json={"data": {"attributes": {"totalMileage": 12345.6}}})
    instance = api.NissanClient("synthetic@example.invalid", "synthetic-password")
    assert instance.fetch_battery() == (47.5, 123.4, MEASUREMENT_UNIX_SECONDS, 12345.6)
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


@pytest.mark.parametrize("soc,bar_units,expected_percent", [
    (0, 0, 0), (0, 1, 0.4166667), (61, 148, 61.6666667),
    (47.5, 114, 47.5), (99, 240, 100), (100, 240, 100),
])
def test_consistent_bar_level_preserves_precision_zero_and_measurement_time(soc, bar_units, expected_percent):
    soc_percent, range_km, timestamp = api.parse_battery(battery(soc, batteryBarLevel=bar_units, rangeHvacOn=0))
    assert soc_percent == pytest.approx(expected_percent)
    assert range_km == 0
    assert timestamp == MEASUREMENT_UNIX_SECONDS


@pytest.mark.parametrize("bar_units", [None, False, -1, 241, "148", {}, [], float("nan"), float("inf")])
def test_invalid_bar_level_retains_valid_battery_level(bar_units):
    assert api.parse_battery(battery(61.25, batteryBarLevel=bar_units))[0] == 61.25


@pytest.mark.parametrize("soc,bar_units", [(1, 0), (80, 12), (0, 240), (50, 122.5)])
def test_inconsistent_bar_level_retains_battery_level(soc, bar_units):
    assert api.parse_battery(battery(soc, batteryBarLevel=bar_units))[0] == soc


@pytest.mark.parametrize("soc", [None, True, -1, 101, "47", float("nan"), float("inf")])
def test_invalid_soc_never_becomes_zero(soc):
    with pytest.raises(api.NissanError):
        api.parse_battery(battery(soc, batteryBarLevel=114))


@pytest.mark.parametrize("timestamp", [None, "bad", "2022-01-01T00:00:00", "2099-01-01T00:00:00Z"])
def test_invalid_timestamp_never_becomes_now(timestamp):
    with pytest.raises(api.NissanError):
        api.parse_battery(battery(timestamp=timestamp, batteryBarLevel=114))


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


@pytest.mark.parametrize("exception_type,message", [
    (requests.ConnectTimeout, "Nissan request timed out."),
    (requests.ReadTimeout, "Nissan request timed out."),
    (requests.exceptions.SSLError, "Nissan TLS connection failed."),
    (requests.ConnectionError, "Nissan connection failed."),
    (requests.RequestException, "Nissan could not be reached."),
])
def test_transport_errors_omit_private_data(http, caplog, exception_type, message):
    caplog.set_level(logging.DEBUG)
    http.get(BATTERY_URL, exc=exception_type("synthetic-private-url"))
    with pytest.raises(api.NissanError) as failure:
        client().fetch_battery()
    assert str(failure.value) == message
    assert failure.value.__suppress_context__
    assert "synthetic-private-url" not in caplog.text
    assert http.call_count == (2 if exception_type is requests.ConnectionError else 1)


@pytest.mark.parametrize("cause_type,wrapper,message", [
    (gaierror, "explicit", "Nissan name resolution failed."),
    (gaierror, "implicit", "Nissan name resolution failed."),
    (ConnectionRefusedError, "explicit", "Nissan connection was refused."),
    (RemoteDisconnected, "protocol", "Nissan connection closed without a response."),
    (ConnectionResetError, "protocol", "Nissan connection was interrupted."),
    (ConnectionAbortedError, "protocol", "Nissan connection was interrupted."),
    (BrokenPipeError, "protocol", "Nissan connection was interrupted."),
])
def test_wrapped_connection_causes_are_classified_without_private_text(http, caplog, cause_type, wrapper, message):
    caplog.set_level(logging.DEBUG)
    cause = cause_type("synthetic-private-url")
    if wrapper == "protocol":
        wrapped = ProtocolError("synthetic-private-url", cause)
    else:
        connection_error = NewConnectionError(None, "synthetic-private-url")
        if wrapper == "explicit":
            connection_error.__cause__ = cause
        else:
            connection_error.__context__ = cause  # Older urllib3 may use implicit chaining.
        wrapped = MaxRetryError(None, "synthetic-private-url", reason=connection_error)
    http.get(BATTERY_URL, exc=requests.ConnectionError(wrapped))
    with pytest.raises(api.NissanError) as failure:
        client().fetch_battery()
    assert str(failure.value) == message
    rendered = "".join(traceback.format_exception(type(failure.value), failure.value, failure.value.__traceback__))
    assert "synthetic-private-url" not in rendered + caplog.text
    assert not api._PRIVATE_HTTP_REQUEST.get()
    assert http.call_count == 2


@pytest.mark.parametrize("chain", ["cycle", "suppressed", "explicit"])
def test_unknown_connection_cause_does_not_guess_from_text_or_unrelated_context(http, chain):
    error = requests.ConnectionError("NameResolutionError: synthetic-private-url")
    error.__context__ = gaierror("synthetic-private-url")
    if chain == "suppressed":
        error.__suppress_context__ = True
    else:
        error.__cause__ = error if chain == "cycle" else OSError("ConnectionRefusedError")
    http.get(BATTERY_URL, exc=error)
    with pytest.raises(api.NissanError, match="^Nissan connection failed[.]$"):
        client().fetch_battery()
    assert http.call_count == 2


@pytest.mark.parametrize("target", [BATTERY_URL, COCKPIT_URL])
def test_vehicle_connection_retry_preserves_session_and_measurements(http, caplog, target):
    caplog.set_level(logging.DEBUG)
    payloads = {BATTERY_URL: battery(batteryBarLevel=114),
                COCKPIT_URL: {"data": {"attributes": {"totalMileage": 0}}}}
    for url, payload in payloads.items():
        http.get(url, json=payload)
    error = requests.ConnectionError(ProtocolError("synthetic-private-url", ConnectionResetError()))
    http.get(target, [{"exc": error}, {"json": payloads[target]}])
    instance = client()
    instance._session.cookies.set("synthetic", "retained")
    manager = instance._session.get_adapter(target).poolmanager
    previous_pool = manager.connection_from_url(target)
    assert instance.fetch_battery() == (47.5, None, MEASUREMENT_UNIX_SECONDS, 0)
    assert http.call_count == 3
    assert manager.connection_from_url(target) is not previous_pool
    assert instance._session.cookies.get("synthetic") == "retained"
    assert instance._access_token == "synthetic-access"
    assert instance._refresh_token == "synthetic-refresh"
    assert instance._session.hooks["response"] == [] and not instance._session.trust_env
    assert caplog.text.count("Nissan vehicle connection failed; retrying once.") == 1
    assert "synthetic-private-url" not in caplog.text
    assert not api._PRIVATE_HTTP_REQUEST.get()


@pytest.mark.parametrize("method,url", [
    ("POST", BATTERY_URL), ("GET", api.AUTH_BASE_URL + "oauth2/authorize"),
    ("POST", REFRESH_URL), ("GET", api.USERS_BASE_URL + "v1/users/current"),
])
def test_connection_retry_is_limited_to_vehicle_gets(http, method, url):
    http.register_uri(method, url, exc=requests.ConnectionError("synthetic-private-url"))
    with pytest.raises(api.NissanError, match="^Nissan connection failed[.]$"):
        client()._request(method, url)
    assert http.call_count == 1


@pytest.mark.parametrize("failure,message", [
    (requests.Timeout, "Nissan request timed out."),
    (requests.exceptions.SSLError, "Nissan TLS connection failed."),
])
def test_second_attempt_preserves_failure_diagnostic(http, failure, message):
    http.get(BATTERY_URL, [{"exc": requests.ConnectionError("synthetic-private-url")},
                           {"exc": failure("synthetic-private-url")}])
    with pytest.raises(api.NissanError) as error:
        client().fetch_battery()
    assert str(error.value) == message
    assert error.value.__suppress_context__
    assert http.call_count == 2


def test_connection_retry_does_not_repeat_authentication(http):
    battery_request = http.get(BATTERY_URL, [{"exc": requests.ConnectionError("synthetic-private-url")},
                                             {"status_code": 401}, {"json": battery()}])
    refresh = http.post(REFRESH_URL, json={"access_token": "synthetic-new"})
    http.get(COCKPIT_URL, json={})
    assert client().fetch_battery()[0] == 47
    assert battery_request.call_count == 3
    assert refresh.call_count == 1


def test_json_errors_omit_private_data(http):
    http.get(BATTERY_URL, text="synthetic-private-body")
    with pytest.raises(api.NissanError, match="^Nissan returned an invalid response.$"):
        client().fetch_battery()


def test_native_configuration_roundtrip_and_private_repr():
    from dataclass_utils import asdict, dataclass_from_dict

    config = NissanConnect(configuration=NissanConnectConfiguration("synthetic@example.invalid", "synthetic-password"))
    assert config.configuration.refresh_while_charging is False
    legacy = asdict(config)
    del legacy["configuration"]["refresh_while_charging"]
    assert dataclass_from_dict(NissanConnect, legacy).configuration.refresh_while_charging is False
    config.configuration.refresh_while_charging = True
    decoded = dataclass_from_dict(NissanConnect, asdict(config))
    assert decoded == config
    assert "synthetic" not in repr(config)
    assert NissanConnect().configuration is not NissanConnect().configuration


@pytest.mark.parametrize("path", [
    "/car-adapter/v1/cars/" + VIN + "/battery-status",
    "/car-adapter/v1/cars/" + VIN + "/actions/status?actionId=synthetic-action",
    "/bff-web/v5/users/synthetic-user/cars",
    "/commonauth?code=synthetic-code&sessionDataKey=synthetic-session",
])
@pytest.mark.parametrize("fail", [False, True])
def test_transport_logs_hide_private_urls_without_muting_other_requests(monkeypatch, caplog, path, fail):
    caplog.set_level(logging.DEBUG)
    instance = client()
    pool = HTTPSConnectionPool("example.invalid")
    connection = Mock(is_closed=False, is_verified=True)
    response = HTTPResponse(status=200, headers={}, preload_content=False)
    response.length = 0
    response.msg = HTTPMessage()
    connection.getresponse.return_value = response
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
        with pytest.raises(api.NissanError, match="^Nissan request timed out.$"):
            instance._request("GET", "https://example.invalid" + path)
    else:
        assert instance._request("GET", "https://example.invalid" + path).status_code == 200
    transport_log.debug("Subsequent request remains visible")
    assert path not in caplog.text
    assert "synthetic-private-url" not in caplog.text
    assert "Other vehicle request remains visible" in caplog.text
    assert "Nissan diagnostic remains visible" in caplog.text
    assert "Subsequent request remains visible" in caplog.text


@pytest.fixture
def active_refresh(http, monkeypatch):
    clock = Mock(return_value=0.0)
    sleep = Mock()
    monkeypatch.setattr(api.time, "monotonic", clock)
    monkeypatch.setattr(api.time, "sleep", sleep)
    instance = client()
    instance._expires_at_monotonic_seconds = float("inf")
    http.post(ACTIVE_REFRESH_URL, json={"data": {"id": "synthetic-action"}})
    http.get(ACTION_STATUS_URL, json={"data": {"attributes": {"status": "completed"}}})
    http.get(BATTERY_URL, json=battery(batteryBarLevel=114))
    http.get(COCKPIT_URL, json={"data": {"attributes": {"totalMileage": 0}}})
    return instance, clock, sleep


@pytest.fixture
def adapter_updater(active_refresh):
    from modules.vehicles import nissanconnect

    instance, _, _ = active_refresh
    factory = Mock()
    # Isolate the adapter from Core's MQTT startup; exercise its real updater and client.
    with patch.dict("sys.modules", {"modules.common.configurable_vehicle": Mock(ConfigurableVehicle=factory)}), \
            patch.object(nissanconnect, "soc", create=True):
        soc = import_module("modules.vehicles.nissanconnect.soc")
        with patch.object(soc, "NissanClient", return_value=instance), \
                patch.object(soc, "ConfigurableVehicle", factory):
            config = NissanConnect(configuration=NissanConnectConfiguration())
            soc.create_vehicle(config, 0)
            yield factory.call_args.kwargs["component_updater"], config.configuration


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("initially_plugged", [False, True])
@pytest.mark.parametrize("command_fails", [False, True])
def test_adapter_plug_in_refresh_and_hourly_charging_limit(
        active_refresh, adapter_updater, http, enabled, initially_plugged, command_fails):
    from modules.common.abstract_vehicle import VehicleUpdateData

    _, clock, _ = active_refresh
    updater, config = adapter_updater
    config.refresh_while_charging = enabled
    if command_fails:
        http.post(ACTIVE_REFRESH_URL, exc=requests.Timeout("synthetic-private-url"))
    for elapsed_seconds, plugged, charging, expected_commands in [
            (0, initially_plugged, False, int(initially_plugged)),
            (10, True, False, 1), (20, True, False, 1), (30, True, True, 1),
            (60, True, False, 1), (70, True, True, 1),  # PV pauses do not create plug-ins.
            (100, False, False, 1), (110, True, False, 2),  # A short drive bypasses the hour.
            (3709, True, True, 2), (3710, True, False, 2), (3710, True, True, 3),
            (3720, False, False, 3), (3730, True, False, 4)]:
        clock.return_value = elapsed_seconds
        state = updater(VehicleUpdateData(plug_state=plugged, charge_state=charging))
        assert state.soc == 47.5 and state.soc_timestamp == MEASUREMENT_UNIX_SECONDS
        assert sum(r.url == ACTIVE_REFRESH_URL for r in http.request_history) == (
            expected_commands if enabled else 0)


def test_failed_battery_read_does_not_replay_plug_in_command(active_refresh, adapter_updater, http):
    from modules.common.abstract_vehicle import VehicleUpdateData

    _, clock, _ = active_refresh
    updater, config = adapter_updater
    config.refresh_while_charging = True
    http.get(BATTERY_URL, [{"exc": requests.Timeout("synthetic-private-url")},
                           {"json": battery(batteryBarLevel=114)}])
    with pytest.raises(api.NissanError):
        updater(VehicleUpdateData(plug_state=True))
    clock.return_value = 10
    assert updater(VehicleUpdateData(plug_state=True)).soc == 47.5
    assert sum(r.url == ACTIVE_REFRESH_URL for r in http.request_history) == 1


@pytest.mark.parametrize("expired_token", [False, True])
@pytest.mark.parametrize("command_fails", [False, True])
def test_refresh_uses_fresh_connection_without_replaying_command(
        active_refresh, http, expired_token, command_fails):
    instance, _, _ = active_refresh
    session = instance._session
    session.cookies.set("synthetic", "retained")
    manager = session.get_adapter(ACTIVE_REFRESH_URL).poolmanager
    previous_pool = manager.connection_from_url(ACTIVE_REFRESH_URL)
    command_pools = []
    expected_token = "synthetic-new" if expired_token else "synthetic-access"

    def authenticate(request, context):
        # Refresh authentication before clearing the connections used by the command.
        assert manager.connection_from_url(ACTIVE_REFRESH_URL) is previous_pool
        return {"access_token": expected_token}

    def command(request, context):
        pool = manager.connection_from_url(ACTIVE_REFRESH_URL)
        assert pool is not previous_pool
        command_pools.append(pool)
        assert request.headers["Authorization"] == "Bearer " + expected_token
        if command_fails:
            raise requests.ConnectionError(ConnectionResetError("synthetic-private"))
        return {"data": {"id": "synthetic-action"}}

    token_request = http.post(REFRESH_URL, json=authenticate)
    command_request = http.post(ACTIVE_REFRESH_URL, json=command)
    with patch.object(session, "close", wraps=session.close) as close:
        # Passive reads preserve the pool; the next eligible command replaces it once.
        assert instance.fetch_battery()[0] == 47.5
        close.assert_not_called()
        if expired_token:
            instance._expires_at_monotonic_seconds = 0
        for _ in range(2):
            assert instance.fetch_battery(refresh_from_vehicle=True)[0] == 47.5
        close.assert_called_once_with()
    assert token_request.call_count == int(expired_token)
    assert command_request.call_count == 1 and len(command_pools) == 1
    assert manager.connection_from_url(ACTIVE_REFRESH_URL) is command_pools[0]
    assert instance._session is session and session.cookies.get("synthetic") == "retained"
    assert instance._access_token == expected_token and instance._refresh_token == "synthetic-refresh"
    assert session.hooks["response"] == [] and not session.trust_env
    assert not api._PRIVATE_HTTP_REQUEST.get()


def test_active_refresh_waits_for_completion_then_reads_original_measurement(active_refresh, http, caplog):
    instance, _, sleep = active_refresh
    caplog.set_level(logging.DEBUG, logger=api.__name__)
    http.get(ACTION_STATUS_URL, [{"json": {"data": {"attributes": {"status": status}}}}
                                 for status in ("pending", "completed")])
    assert instance.fetch_battery(refresh_from_vehicle=True) == (47.5, None, MEASUREMENT_UNIX_SECONDS, 0)
    assert [r.url for r in http.request_history] == [
        ACTIVE_REFRESH_URL, ACTION_STATUS_URL, ACTION_STATUS_URL, BATTERY_URL, COCKPIT_URL]
    command = http.request_history[0]
    assert command.method == "POST" and command.json() == {"data": {"type": "RefreshBatteryStatus"}}
    assert command.headers["Authorization"] == "Bearer synthetic-access"
    assert command.headers["Content-Type"] == api.JSON_API_CONTENT_TYPE
    sleep.assert_called_once_with(api.BATTERY_REFRESH_POLL_INTERVAL_SECONDS)
    assert [record.getMessage() for record in caplog.records if record.name == api.__name__] == [
        "Requesting Nissan battery refresh.", "Nissan battery refresh completed.",
        f"Nissan battery measurement_unix_seconds={MEASUREMENT_UNIX_SECONDS}",
    ]
    assert all(value not in caplog.text for value in (VIN, "synthetic-action", "synthetic-access"))


@pytest.mark.parametrize("url,response", [
    (ACTIVE_REFRESH_URL, {"exc": requests.ConnectionError("synthetic-private-url")}),
    (ACTIVE_REFRESH_URL, {"exc": requests.Timeout("synthetic-private-url")}),
    (ACTIVE_REFRESH_URL, {"status_code": 401}),
    (ACTIVE_REFRESH_URL, {"status_code": 429}),
    (ACTIVE_REFRESH_URL, {"status_code": 503}),
    (ACTIVE_REFRESH_URL, {"text": "synthetic-private-body"}),
    (ACTIVE_REFRESH_URL, {"json": ["synthetic-private"]}),
    (ACTIVE_REFRESH_URL, {"json": {"errors": [{"detail": "synthetic-private"}]}}),
    (ACTIVE_REFRESH_URL, {"json": {"error": "synthetic-private"}}),
    (ACTIVE_REFRESH_URL, {"json": {"private": "synthetic-private"}}),
    (ACTIVE_REFRESH_URL, {"json": {"data": {"id": None}}}),
    (ACTIVE_REFRESH_URL, {"json": {"data": {"id": ""}}}),
    (ACTIVE_REFRESH_URL, {"json": {"data": []}}),
    (ACTION_STATUS_URL, {"exc": requests.exceptions.SSLError("synthetic-private-url")}),
    (ACTION_STATUS_URL, {"exc": requests.RequestException("synthetic-private-url")}),
    (ACTION_STATUS_URL, {"status_code": 429}),
    (ACTION_STATUS_URL, {"status_code": 503}),
    (ACTION_STATUS_URL, {"text": "synthetic-private-body"}),
    (ACTION_STATUS_URL, {"json": {"data": {"attributes": {"status": None}}}}),
    (ACTION_STATUS_URL, {"json": {}}),
    (ACTION_STATUS_URL, {"json": {"data": []}}),
])
def test_failed_refresh_preserves_passive_reads_and_hourly_limit(active_refresh, http, caplog, url, response):
    instance, clock, _ = active_refresh
    caplog.set_level(logging.DEBUG, logger=api.__name__)
    http.register_uri("POST" if url == ACTIVE_REFRESH_URL else "GET", url, **response)
    for elapsed_seconds in (0, 600, 3599, 3600):
        clock.return_value = elapsed_seconds
        assert instance.fetch_battery(refresh_from_vehicle=True) == (47.5, None, MEASUREMENT_UNIX_SECONDS, 0)
        assert sum(r.url == ACTIVE_REFRESH_URL for r in http.request_history) == (2 if elapsed_seconds == 3600 else 1)
    if url == ACTION_STATUS_URL:
        assert sum(r.url == ACTION_STATUS_URL for r in http.request_history) == 2  # One poll per hourly attempt.
    assert "Nissan battery refresh failed; reading cached data." in caplog.text
    assert all(value not in caplog.text for value in (VIN, "synthetic-action", "synthetic-private"))


@pytest.mark.parametrize("status", ["pending", "synthetic-private", "failed", "cancelled"])
def test_refresh_polling_is_bounded_and_terminal_failure_stops_early(active_refresh, http, caplog, status):
    instance, _, sleep = active_refresh
    caplog.set_level(logging.DEBUG, logger=api.__name__)
    poll = http.get(ACTION_STATUS_URL, json={"data": {"attributes": {"status": status}}})
    assert instance.fetch_battery(refresh_from_vehicle=True)[0] == 47.5
    expected_polls = 1 if status in ("failed", "cancelled") else api.MAX_BATTERY_REFRESH_POLLS
    assert poll.call_count == expected_polls
    assert sleep.call_count == expected_polls - 1
    outcome = status if status in ("failed", "cancelled") else "did not complete"
    assert f"Nissan battery refresh {outcome}; reading cached data." in caplog.text
    assert all(value not in caplog.text for value in (VIN, "synthetic-action", "synthetic-private"))


def test_status_authentication_retry_never_replays_refresh_command(active_refresh, http, caplog):
    instance, _, _ = active_refresh
    caplog.set_level(logging.DEBUG, logger=api.__name__)
    poll = http.get(ACTION_STATUS_URL, [{"status_code": 401},
                                        {"json": {"data": {"attributes": {"status": "completed"}}}}])
    token = http.post(REFRESH_URL, json={"access_token": "synthetic-new"})
    assert instance.fetch_battery(refresh_from_vehicle=True)[0] == 47.5
    assert poll.call_count == 2 and token.call_count == 1
    assert all(value not in caplog.text for value in (VIN, "synthetic-new", "synthetic-action"))
    assert sum(r.url == ACTIVE_REFRESH_URL for r in http.request_history) == 1


@pytest.mark.parametrize("exception_type,requests_per_failed_poll", [
    (requests.ConnectionError, 2), (requests.ConnectTimeout, 1), (requests.ReadTimeout, 1),
])
@pytest.mark.parametrize("recovers", [True, False])
def test_status_transport_failures_consume_bounded_polls_without_replaying_command(
        active_refresh, http, caplog, exception_type, requests_per_failed_poll, recovers):
    instance, clock, sleep = active_refresh
    caplog.set_level(logging.DEBUG, logger=api.__name__)
    responses = [{"exc": exception_type("synthetic-private-url")}] * requests_per_failed_poll
    if recovers:
        responses.append({"json": {"data": {"attributes": {"status": "completed"}}}})
    poll = http.get(ACTION_STATUS_URL, responses)
    assert instance.fetch_battery(refresh_from_vehicle=True) == (47.5, None, MEASUREMENT_UNIX_SECONDS, 0)
    expected_requests = requests_per_failed_poll + 1 if recovers else (
        requests_per_failed_poll * api.MAX_BATTERY_REFRESH_POLLS)
    assert poll.call_count == expected_requests
    assert sleep.call_count == (1 if recovers else api.MAX_BATTERY_REFRESH_POLLS - 1)
    assert all(call.args == (api.BATTERY_REFRESH_POLL_INTERVAL_SECONDS,) for call in sleep.call_args_list)
    assert ("Nissan battery refresh completed." in caplog.text) is recovers
    assert "Nissan battery refresh status transport error." in caplog.text
    assert all(value not in caplog.text for value in (VIN, "synthetic-action", "synthetic-private"))
    clock.return_value = 600
    assert instance.fetch_battery(refresh_from_vehicle=True)[0] == 47.5
    assert poll.call_count == expected_requests
    assert sum(r.url == ACTIVE_REFRESH_URL for r in http.request_history) == 1


def test_refresh_authentication_failure_does_not_submit_command_or_log_private_data(active_refresh, http, caplog):
    instance, _, _ = active_refresh
    caplog.set_level(logging.DEBUG, logger=api.__name__)
    instance._expires_at_monotonic_seconds = -1
    http.post(REFRESH_URL, status_code=503, text="synthetic-private")
    instance._refresh_battery(api.CARS_BASE_URL + "v1/cars/" + VIN)
    assert all(r.url != ACTIVE_REFRESH_URL for r in http.request_history)
    assert "Nissan battery refresh failed; reading cached data." in caplog.text
    assert not api._PRIVATE_HTTP_REQUEST.get()
    assert all(value not in caplog.text for value in (
        VIN, "synthetic-private", "synthetic-refresh", "synthetic-access", "synthetic-password"))
