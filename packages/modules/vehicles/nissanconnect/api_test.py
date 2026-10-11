"""Synthetic fixtures only. No captured account responses or real identifiers."""
import base64
import hashlib
import io
import logging
import traceback
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from modules.vehicles.nissanconnect.src.api import (
    AUTH_BASE_URL, CARS_BASE_URL, AuthenticationError, MAX_RESPONSE_BYTES,
    NissanError, PrivateTransport, RateLimitError, parse_battery)
from modules.vehicles.nissanconnect.tests.helpers import (
    FORM, MEASURED_UNIX_SECONDS, SECOND_VIN, VIN, battery, full_script, login_script, make_client, reply)


@pytest.mark.parametrize("soc", [0, 47.5, 100])
def test_valid_soc_preserves_old_measurement(soc):
    result = parse_battery(battery(soc, rangeHvacOn=0, rangeHvacOff=150),
                           now_unix_seconds=MEASURED_UNIX_SECONDS + 86400)
    assert (result.soc_percent, result.measurement_unix_seconds, result.range_km) == (soc, MEASURED_UNIX_SECONDS, 0)


@pytest.mark.parametrize("soc", [None, True, False, -1, 101, "47", float("nan"), float("inf"), [], {}])
def test_invalid_soc_never_becomes_zero(soc):
    with pytest.raises(NissanError):
        parse_battery(battery(soc), now_unix_seconds=MEASURED_UNIX_SECONDS)


@pytest.mark.parametrize("timestamp", [None, 0, "", "bad", "2022-01-01T00:00:00", "2099-01-01T00:00:00Z"])
def test_missing_ambiguous_or_future_time_rejected(timestamp):
    with pytest.raises(NissanError):
        parse_battery(battery(timestamp=timestamp), now_unix_seconds=MEASURED_UNIX_SECONDS)


def test_offset_time_and_optional_range():
    result = parse_battery(battery(timestamp="2022-01-01T01:00:00+01:00", rangeHvacOff=150),
                           now_unix_seconds=MEASURED_UNIX_SECONDS)
    assert result.measurement_unix_seconds == MEASURED_UNIX_SECONDS
    assert result.range_km == 150
    assert parse_battery(battery(rangeHvacOn=-1), now_unix_seconds=MEASURED_UNIX_SECONDS).range_km is None


@pytest.mark.parametrize("body", [{}, {"data": None}, {"data": {"attributes": {}}}, [], None])
def test_invalid_shape_has_safe_error(body):
    with pytest.raises(NissanError):
        parse_battery(body)


def test_login_pkce_selection_and_cached_battery_only(caplog):
    caplog.set_level(logging.DEBUG)
    client, transport, _ = make_client(full_script())
    status = client.fetch_battery()
    assert (status.soc_percent == 47 and status.measurement_unix_seconds == MEASURED_UNIX_SECONDS
            and status.range_km == 123.4)
    calls = transport.calls
    authorize = parse_qs(urlsplit(calls[0][1]).query)
    verifier = calls[2][2]["form"]["code_verifier"]
    expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    assert authorize["code_challenge"] == [expected]
    assert authorize["code_challenge_method"] == ["S256"]
    assert calls[1][2]["form"]["username"] == "EU/synthetic@example.invalid"
    assert calls[3][2]["headers"]["Authorization"] == "synthetic-id"
    assert calls[-1][2]["headers"]["Authorization"] == "Bearer synthetic-access"
    assert calls[-1][:2] == ("GET", CARS_BASE_URL + "v1/cars/" + VIN + "/battery-status")
    assert all("/actions/" not in url for _, url, _ in calls)
    assert all(0 < kwargs["timeout_seconds"] <= 10 for _, _, kwargs in calls)
    assert not caplog.records
    assert not transport.responses


def test_subsequent_update_reuses_tokens_and_vehicle():
    client, transport, _ = make_client(full_script() + [reply(battery(48))])
    client.fetch_battery()
    count = len(transport.calls)
    assert client.fetch_battery().soc_percent == 48
    assert len(transport.calls) == count + 1


def test_expired_token_is_refreshed_in_memory():
    script = full_script() + [reply({"access_token": "synthetic-renewed"}), reply(battery())]
    client, transport, ticks_monotonic_seconds = make_client(script)
    client.fetch_battery()
    ticks_monotonic_seconds[0] = 3600
    client.fetch_battery()
    assert "refresh-token" in transport.calls[-2][1]
    assert transport.calls[-2][2]["headers"]["Authorization"] == "synthetic-refresh"
    assert transport.calls[-1][2]["headers"]["Authorization"] == "Bearer synthetic-renewed"


def test_rejected_refresh_logs_in_once():
    script = full_script() + [reply({"error": "invalid_grant"}, 400)] + login_script() + [reply(battery())]
    client, transport, ticks_monotonic_seconds = make_client(script)
    client.fetch_battery()
    ticks_monotonic_seconds[0] = 3600
    client.fetch_battery()
    assert sum("oauth2/authorize?" in url for _, url, _ in transport.calls) == 2
    assert transport.cookies_cleared == 2


def test_401_retries_once_then_stops_and_cools_down():
    script = full_script() + [reply("synthetic-private-body", 401), reply({"access_token": "synthetic-new"}),
                              reply("synthetic-private-body", 401)]
    client, transport, _ = make_client(script)
    client.fetch_battery()
    with pytest.raises(AuthenticationError, match="Nissan"):
        client.fetch_battery()
    count = len(transport.calls)
    with pytest.raises(AuthenticationError, match="paused"):
        client.fetch_battery()
    assert len(transport.calls) == count


def test_state_mismatch_never_exchanges_tokens():
    client, transport, _ = make_client([reply(FORM), reply("", 302, {
        "Location": "com://wso2.service.nci?code=synthetic-code&state=wrong"})])
    with pytest.raises(AuthenticationError):
        client.fetch_battery()
    assert len(transport.calls) == 2


@pytest.mark.parametrize("target", [
    "https://example.invalid/steal", "http://login.mynissan-account.com/",
    "https://login.mynissan-account.com:444/", "https://user@login.mynissan-account.com/",
])
def test_form_target_validated_before_sending_credentials(target):
    client, transport, _ = make_client([reply(FORM.replace("/commonauth", target))])
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 1


def test_cross_origin_redirect_is_never_followed():
    client, transport, _ = make_client([reply("", 302, {"Location": "https://example.invalid/steal"})])
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 1


def test_redirect_loop_is_bounded():
    client, transport, _ = make_client([reply("", 302, {"Location": "/loop"})] * 11)
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 11


@pytest.mark.parametrize("vehicles,vin", [
    ([], None), ([{"vin": VIN}, {"vin": SECOND_VIN}], None), ([{"vin": VIN}], SECOND_VIN),
])
def test_missing_or_ambiguous_vehicle_never_guessed(vehicles, vin):
    client, transport, _ = make_client(full_script(vehicles), vin)
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert not any("battery-status" in url for _, url, _ in transport.calls)


def test_configured_vehicle_is_selected():
    client, transport, _ = make_client(full_script([{"vin": VIN}, {"vin": SECOND_VIN}]), SECOND_VIN.lower())
    client.fetch_battery()
    assert SECOND_VIN in transport.calls[-1][1]


def test_rate_limit_pauses_later_updates_without_sleeping():
    client, transport, ticks_monotonic_seconds = make_client(
        full_script() + [reply("private", 429, {"Retry-After": "600"})])
    client.fetch_battery()
    with pytest.raises(RateLimitError):
        client.fetch_battery()
    ticks_monotonic_seconds[0] = 599
    count = len(transport.calls)
    with pytest.raises(RateLimitError):
        client.fetch_battery()
    assert len(transport.calls) == count
    ticks_monotonic_seconds[0] = 600
    transport.responses.append(reply(battery()))
    assert client.fetch_battery().soc_percent == 47


@pytest.mark.parametrize("response", [
    reply("private", 500), reply("private", 503), reply("not-json"),
    reply({"errors": [{"detail": "private"}]}), reply({"id_token": None}),
])
def test_bad_response_not_logged_or_in_error(response, caplog):
    caplog.set_level(logging.DEBUG)
    script = login_script()
    script[2] = response
    client, _, _ = make_client(script)
    with pytest.raises(NissanError) as error:
        client.fetch_battery()
    assert "private" not in str(error.value)
    assert "synthetic-password" not in str(error.value)
    assert not caplog.records


def test_transport_hides_exception_details_and_response_repr(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    transport = PrivateTransport()
    private_value = "synthetic-secret-value"

    def fail(*args, **kwargs):
        raise URLError(private_value)

    monkeypatch.setattr(transport._opener, "open", fail)
    with pytest.raises(NissanError) as error:
        transport.request("GET", AUTH_BASE_URL)
    formatted = "".join(traceback.format_exception(type(error.value), error.value, error.value.__traceback__))
    assert private_value not in formatted
    assert private_value not in repr(reply(private_value, headers={"Authorization": private_value}))
    assert not caplog.records


def test_transport_returns_redirect_without_following(monkeypatch):
    transport = PrivateTransport()

    def respond(*args, **kwargs):
        raise HTTPError(AUTH_BASE_URL, 302, "redirect", {"Location": "/next"}, io.BytesIO(b""))

    monkeypatch.setattr(transport._opener, "open", respond)
    result = transport.request("GET", AUTH_BASE_URL)
    assert result.status == 302 and result.headers["Location"] == "/next"


def test_transport_limits_response_size(monkeypatch):
    transport = PrivateTransport()

    def respond(*args, **kwargs):
        raise HTTPError(AUTH_BASE_URL, 500, "error", {}, io.BytesIO(b"x" * (MAX_RESPONSE_BYTES + 1)))

    monkeypatch.setattr(transport._opener, "open", respond)
    with pytest.raises(NissanError, match="too large"):
        transport.request("GET", AUTH_BASE_URL)


def test_total_request_budget_stops_redirect_chain():
    client, transport, ticks_monotonic_seconds = make_client([])

    def slow_response(calls):
        ticks_monotonic_seconds[0] += 61
        return reply("", 302, {"Location": "/next"})

    transport.responses.append(slow_response)
    with pytest.raises(NissanError, match="time limit"):
        client.fetch_battery()
    assert len(transport.calls) == 1


@pytest.mark.parametrize("response", [
    reply("synthetic-private-body", 500), reply("synthetic-private-body", 503),
    reply("not-json"), reply(battery(soc=None)),
])
def test_failed_query_pauses_without_reauthentication_and_recovers(response, caplog):
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [response, reply(battery(48))])
    client.fetch_battery()
    with pytest.raises(NissanError):
        client.fetch_battery()
    count = len(transport.calls)
    ticks_monotonic_seconds[0] = 299
    with pytest.raises(NissanError, match="paused") as error:
        client.fetch_battery()
    assert len(transport.calls) == count
    assert "synthetic-private-body" not in str(error.value)
    ticks_monotonic_seconds[0] = 300
    assert client.fetch_battery().soc_percent == 48
    assert len(transport.calls) == count + 1
    assert not caplog.records


def test_repeated_outages_back_off_to_one_hour_and_success_resets_delay():
    client, transport, ticks_monotonic_seconds = make_client(full_script())
    client.fetch_battery()
    for delay_seconds in (300, 600, 1200, 2400, 3600, 3600):
        transport.responses.append(reply("synthetic-private-body", 503))
        with pytest.raises(NissanError):
            client.fetch_battery()
        count = len(transport.calls)
        ticks_monotonic_seconds[0] += delay_seconds - 1
        with pytest.raises(NissanError, match="paused"):
            client.fetch_battery()
        assert len(transport.calls) == count
        ticks_monotonic_seconds[0] += 1
        # Keep the synthetic token alive; expiry/renewal is tested separately.
        client._expires_at_monotonic_seconds = ticks_monotonic_seconds[0] + 7200
    transport.responses.extend([reply(battery(49)), reply("private", 503)])
    assert client.fetch_battery().soc_percent == 49
    with pytest.raises(NissanError):
        client.fetch_battery()
    ticks_monotonic_seconds[0] += 300
    transport.responses.append(reply(battery(50)))
    assert client.fetch_battery().soc_percent == 50


@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.parametrize("header,expected_delay", [
    ("1200", 1200), ("Sun, 02 Jan 2022 00:20:00 GMT", 1200),
    ("Sun, 02 Jan 2022 00:01:00 GMT", 300), ("-1", 300), ("bad-date", 300),
])
def test_retry_after_seconds_and_http_date_are_respected(status, header, expected_delay):
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [
        reply("private", status, {"rEtRy-AfTeR": header}), reply(battery())])
    client.fetch_battery()
    with pytest.raises(NissanError):
        client.fetch_battery()
    count = len(transport.calls)
    ticks_monotonic_seconds[0] = expected_delay - 1
    with pytest.raises(NissanError, match="paused"):
        client.fetch_battery()
    assert len(transport.calls) == count
    ticks_monotonic_seconds[0] = expected_delay
    assert client.fetch_battery().soc_percent == 47


def test_timeout_pauses_requests_without_retaining_exception_traceback():
    def timeout(calls):
        raise NissanError("Nissan is unreachable or returned an invalid response.")
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [timeout, reply(battery())])
    client.fetch_battery()
    with pytest.raises(NissanError):
        client.fetch_battery()
    count = len(transport.calls)
    for _ in range(5):
        with pytest.raises(NissanError, match="paused"):
            client.fetch_battery()
    assert len(transport.calls) == count
    assert not any(isinstance(value, BaseException) for value in vars(client).values())
    ticks_monotonic_seconds[0] = 300
    assert client.fetch_battery().soc_percent == 47


def test_unrepresentable_optional_range_preserves_valid_soc():
    result = parse_battery(battery(rangeHvacOn=10 ** 400), now_unix_seconds=MEASURED_UNIX_SECONDS)
    assert (result.soc_percent, result.measurement_unix_seconds, result.range_km) == (47, MEASURED_UNIX_SECONDS, None)


def test_unrepresentable_token_lifetime_is_safe_and_pauses_retry():
    script = login_script()
    script[-1] = reply({"access_token": "synthetic-private-access", "expires_in": 10 ** 400})
    client, transport, _ = make_client(script)
    with pytest.raises(AuthenticationError, match="token lifetime") as error:
        client.fetch_battery()
    assert "synthetic-private-access" not in str(error.value)
    assert client._access_token is None and client._refresh_token is None
    count = len(transport.calls)
    with pytest.raises(AuthenticationError, match="paused"):
        client.fetch_battery()
    assert len(transport.calls) == count


@pytest.mark.parametrize("during_form", [False, True])
def test_malformed_login_destination_is_safe_and_pauses_retry(during_form):
    private_url = "https://[synthetic-private-host"
    response = reply(FORM.replace("/commonauth", private_url)) if during_form else reply(
        "", 302, {"Location": private_url})
    client, transport, _ = make_client([response])
    with pytest.raises(NissanError) as error:
        client.fetch_battery()
    assert "synthetic-private-host" not in str(error.value)
    with pytest.raises(NissanError, match="paused"):
        client.fetch_battery()
    assert len(transport.calls) == 1


def test_rotated_refresh_token_is_used_on_next_expiry():
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [
        reply({"access_token": "synthetic-next-access", "refresh_token": "synthetic-next-refresh"}),
        reply(battery()), reply({"access_token": "synthetic-final-access"}), reply(battery())])
    client.fetch_battery()
    ticks_monotonic_seconds[0] = 3600
    client.fetch_battery()
    ticks_monotonic_seconds[0] = 7200
    client.fetch_battery()
    assert transport.calls[-2][2]["headers"]["Authorization"] == "synthetic-next-refresh"
    assert transport.calls[-1][2]["headers"]["Authorization"] == "Bearer synthetic-final-access"


def test_refresh_service_failure_does_not_fall_back_to_password_login():
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [reply("synthetic-private-body", 503)])
    client.fetch_battery()
    ticks_monotonic_seconds[0] = 3600
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert len(transport.calls) == 8
    assert "refresh-token" in transport.calls[-1][1]
    with pytest.raises(NissanError, match="paused"):
        client.fetch_battery()
    assert len(transport.calls) == 8
