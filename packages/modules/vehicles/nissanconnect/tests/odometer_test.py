"""Optional odometer contracts with invented values and a blocked network."""
import json

import pytest

from modules.vehicles.nissanconnect.src.api import CARS_BASE_URL, NissanError, RateLimitError, parse_odometer
from modules.vehicles.nissanconnect.tests.helpers import VIN, battery, full_script, make_client, reply
from modules.vehicles.nissanconnect.connection_test import run_test


def cockpit(value=12345.6, **extra):
    return {"data": {"attributes": dict(totalMileage=value, **extra)}}


@pytest.mark.parametrize("value", [0, 12345, 12345.6])
def test_only_total_mileage_is_used_in_kilometres(value):
    assert parse_odometer(cockpit(value, mileage=99, rangeHvacOn=321)) == value


@pytest.mark.parametrize("value", [None, True, False, -1, "12345", [], {}, float("nan"), float("inf"), 10 ** 400])
def test_invalid_odometer_is_absent_instead_of_zero(value):
    assert parse_odometer(cockpit(value)) is None


@pytest.mark.parametrize("body", [None, [], {}, {"data": None}, {"data": {"attributes": []}},
                                  {"data": {"attributes": {"mileage": 12345}}}])
def test_missing_odometer_and_malformed_shapes_are_optional(body):
    assert parse_odometer(body) is None


def test_passive_query_preserves_battery_time_and_does_not_reuse_old_odometer():
    client, transport, ticks_monotonic_seconds = make_client(
        full_script() + [reply(cockpit()), reply(battery()), reply(cockpit(None))])
    first = client.fetch_battery(include_odometer=True)
    assert first.odometer_km == 12345.6
    assert first.measurement_unix_seconds == 1640995200
    assert transport.calls[-1][:2] == ("GET", CARS_BASE_URL + "v1/cars/" + VIN + "/cockpit")
    assert transport.calls[-1][2]["headers"]["Authorization"] == "Bearer synthetic-access"
    assert client.last_query["odometer_outcome"] == "success"
    assert client.last_query["odometer_http_status"] == 200
    assert client.last_query["odometer_received_at"] == "2022-01-02T00:00:00+00:00"
    assert client.last_query["measurement_at"] == "2022-01-01T00:00:00+00:00"
    ticks_monotonic_seconds[0] = 10
    second = client.fetch_battery(include_odometer=True)
    assert second.soc_percent == 47 and second.odometer_km is None
    assert client.last_query["odometer_outcome"] == "unavailable"
    assert client.last_query["odometer_received_at"] is None
    assert all("/actions/" not in url for _, url, _ in transport.calls)
    assert not transport.responses


@pytest.mark.parametrize("status", [401, 403, 404, 500, 503])
def test_optional_http_error_keeps_soc_and_does_not_repeat_login_or_block_battery(status):
    script = full_script() + [reply("synthetic-private-body", status), reply(battery(48)),
                              reply(battery(49)), reply(cockpit(12346))]
    client, transport, ticks_monotonic_seconds = make_client(script)
    result = client.fetch_battery(include_odometer=True)
    assert result.soc_percent == 47 and result.odometer_km is None
    assert len(transport.calls) == 8
    assert client.last_query["outcome"] == "success"
    assert client.last_query["odometer_outcome"] == "failed"
    assert client.last_query["odometer_http_status"] == status
    assert client.last_query["retry_after_seconds"] == 0
    assert "synthetic-private-body" not in json.dumps(client.last_query)
    ticks_monotonic_seconds[0] = 10
    assert client.fetch_battery(include_odometer=True).soc_percent == 48
    assert len(transport.calls) == 9
    assert client.last_query["odometer_outcome"] == "deferred"
    assert client.last_query["odometer_http_status"] is None
    assert client.last_query["odometer_retry_after_seconds"] == 290
    ticks_monotonic_seconds[0] = 300
    assert client.fetch_battery(include_odometer=True).odometer_km == 12346
    assert len(transport.calls) == 11
    assert not transport.responses


@pytest.mark.parametrize("status,headers,pause,error_type", [
    (429, {}, 300, RateLimitError), (429, {"Retry-After": "900"}, 900, RateLimitError),
    (503, {"Retry-After": "600"}, 600, NissanError)])
def test_provider_pause_from_optional_query_survives_battery_success(status, headers, pause, error_type):
    script = full_script() + [reply({}, status, headers), reply(battery()), reply(cockpit())]
    client, transport, ticks_monotonic_seconds = make_client(script)
    assert client.fetch_battery(include_odometer=True).soc_percent == 47
    assert client.last_query["provider_retry_after_seconds"] == pause
    count = len(transport.calls)
    with pytest.raises(error_type, match="paused"):
        client.fetch_battery(include_odometer=True)
    assert len(transport.calls) == count
    assert client.last_query["odometer_km"] is None
    assert client.last_query["odometer_outcome"] == "not_requested"
    ticks_monotonic_seconds[0] = pause
    assert client.fetch_battery(include_odometer=True).odometer_km == 12345.6
    assert client.last_query["provider_retry_after_seconds"] == 0


@pytest.mark.parametrize("body", ["invalid synthetic JSON", {"errors": ["synthetic-private-body"]}])
def test_bad_optional_response_keeps_successful_battery(body):
    client, _, _ = make_client(full_script() + [reply(body)])
    assert client.fetch_battery(include_odometer=True).soc_percent == 47
    assert client.last_query["odometer_outcome"] == "failed"
    assert "synthetic-private-body" not in json.dumps(client.last_query)


def test_optional_transport_error_keeps_successful_battery():
    def timeout(calls):
        raise NissanError("Synthetic transport timeout.")
    client, _, _ = make_client(full_script() + [timeout])
    assert client.fetch_battery(include_odometer=True).soc_percent == 47
    assert client.last_query["odometer_http_status"] is None
    assert client.last_query["outcome"] == "success"


def test_no_cockpit_request_after_battery_failure_or_exhausted_budget():
    client, transport, _ = make_client(full_script()[:-1] + [reply(battery(None))])
    with pytest.raises(NissanError):
        client.fetch_battery(include_odometer=True)
    assert not any(url.endswith("/cockpit") for _, url, _ in transport.calls)
    client, transport, ticks_monotonic_seconds = make_client(full_script())

    def slow_battery(calls):
        ticks_monotonic_seconds[0] = 61
        return reply(battery())
    transport.responses[-1] = slow_battery
    assert client.fetch_battery(include_odometer=True).soc_percent == 47
    assert len(transport.calls) == 7
    assert client.last_query["odometer_outcome"] == "failed"


def test_unsaved_test_accepts_partial_success_and_preserves_provider_pause():
    client, _, _ = make_client(full_script() + [reply({}, 429, {"Retry-After": "900"})])
    result = run_test({"user_id": "synthetic@example.invalid", "password": "synthetic-password"},
                      client_factory=lambda *args: client)
    assert result["success"] is True and result["query"]["soc"] == 47
    assert result["query"]["odometer_km"] is None
    assert result["query"]["provider_retry_after_seconds"] == 900
    for secret in (VIN, "synthetic-password", "synthetic-access", "example.invalid"):
        assert secret not in json.dumps(result)


def test_zero_retry_after_does_not_remove_rate_limit_backoff():
    client, transport, _ = make_client(full_script() + [reply({}, 429, {"Retry-After": "0"})])
    assert client.fetch_battery(include_odometer=True).soc_percent == 47
    assert client.last_query["retry_after_seconds"] == 300
    with pytest.raises(RateLimitError, match="paused"):
        client.fetch_battery(include_odometer=True)
    assert len(transport.calls) == 8
