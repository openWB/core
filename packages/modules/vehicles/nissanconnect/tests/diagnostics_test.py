"""Synthetic query diagnostics and isolated settings-worker contracts."""
from datetime import datetime
import json
import time
from unittest.mock import Mock

import pytest

from modules.vehicles.nissanconnect.src.api import AuthenticationError, NissanError, RequestCounter
from modules.vehicles.nissanconnect.tests.helpers import MEASURED_UNIX_SECONDS, VIN, full_script, make_client, reply
from modules.vehicles.nissanconnect.connection_test import run_test


def test_diagnostics_distinguish_contact_measurement_failure_and_deferred_update():
    client, transport, ticks_monotonic_seconds = make_client(full_script() + [reply('synthetic-private-body', 503)])
    client._unix_seconds = lambda: MEASURED_UNIX_SECONDS + 86400 + ticks_monotonic_seconds[0]
    client.fetch_battery()
    success = client.last_query.copy()
    assert success['outcome'] == 'success'
    assert success['http_requests'] == 7
    assert success['measurement_at'] == '2022-01-01T00:00:00+00:00'
    assert success['request_started_at'] == '2022-01-02T00:00:00+00:00'
    assert success['data_age_seconds'] == 86400
    assert (success['soc'], success['range_km']) == (47, 123.4)
    ticks_monotonic_seconds[0] = 10
    with pytest.raises(NissanError):
        client.fetch_battery()
    failure = client.last_query.copy()
    assert failure['outcome'] == 'failed'
    assert failure['last_http_status'] == 503
    assert failure['soc'] is None and failure['measurement_at'] is None
    assert failure['last_success_at'] == success['completed_at']
    assert failure['last_measurement_at'] == success['measurement_at']
    ticks_monotonic_seconds[0] = 20
    requests = len(transport.calls)
    with pytest.raises(NissanError):
        client.fetch_battery()
    deferred = client.last_query
    assert deferred['outcome'] == 'deferred'
    assert deferred['http_requests'] == 0 and deferred['request_started_at'] is None
    assert deferred['last_contact_at'] == failure['last_contact_at']
    assert deferred['last_success_at'] == success['completed_at']
    assert len(transport.calls) == requests
    for value in ('synthetic-private-body', 'synthetic-password', VIN, 'synthetic-access', 'example.invalid'):
        assert value not in json.dumps([success, failure, deferred])


def test_worker_returns_only_query_result_and_does_not_log(caplog):
    client, transport, _ = make_client(full_script() + [reply({"data": {"attributes": {"totalMileage": 12345.6}}})])
    result = run_test({'user_id': 'synthetic@example.invalid', 'password': 'synthetic-password'},
                      client_factory=lambda *args: client)
    assert result['success'] is True
    assert result['query']['soc'] == 47
    assert result['query']['data_age_seconds'] == 86400
    assert len(transport.calls) == 8
    assert result["query"]["odometer_km"] == 12345.6
    assert not caplog.records
    for value in ('synthetic-password', 'example.invalid', VIN, 'synthetic-access'):
        assert value not in json.dumps(result)


@pytest.mark.parametrize('payload', [
    None, [], {}, {'user_id': 'a', 'password': 'p', 'url': 'https://invalid/'},
    {'user_id': 'a', 'password': 'p', 'vin': []},
    {'user_id': 'a', 'password': 'p', 'vin': 'wrong'},
    {'user_id': 'a', 'password': 'p' * 4097}])
def test_worker_rejects_invalid_input_without_creating_client(payload):
    factory = Mock()
    assert run_test(payload, factory) == {'success': False, 'code': 'invalid_input'}
    factory.assert_not_called()


@pytest.mark.parametrize('error,code', [
    (AuthenticationError('synthetic-private'), 'authentication_failed'),
    (NissanError('synthetic-private'), 'query_failed'),
    (RuntimeError('synthetic-private'), 'internal_error')])
def test_worker_never_echoes_error_details(error, code):
    client = Mock(last_query=None)
    client.fetch_battery.side_effect = error
    result = run_test({'user_id': 'a', 'password': 'p'}, lambda *args: client)
    assert result['success'] is False and result['code'] == code
    assert 'synthetic-private' not in json.dumps(result)


@pytest.mark.parametrize('status,headers,expected', [
    (401, {}, 0), (503, {}, 0), (503, {'Retry-After': 'bad'}, 0),
    (503, {'Retry-After': '60'}, 60), (429, {}, 300), (429, {'Retry-After': '900'}, 900)])
def test_provider_advice_is_separate_from_scheduled_error_backoff(status, headers, expected):
    client, _, _ = make_client([reply({}, status, headers)])
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert client.last_query['provider_retry_after_seconds'] == expected
    assert client.last_query['retry_after_seconds'] == max(300, expected)


def test_login_success_followed_by_battery_failure_is_not_a_successful_test():
    client, _, _ = make_client(full_script()[:-1] + [reply({}, 503)])
    result = run_test({'user_id': 'synthetic@example.invalid', 'password': 'synthetic-password'},
                      client_factory=lambda *args: client)
    assert result['success'] is False
    assert result['query']['phase'] == 'battery'
    assert result['query']['provider_retry_after_seconds'] == 0


def test_request_totals_separate_rolling_window_from_local_day():
    start_unix_seconds = datetime(2022, 1, 1, 23, 59, 50).timestamp()
    counter = RequestCounter()
    counter.record(0, start_unix_seconds)
    counter.record(20, start_unix_seconds + 20)
    after_midnight = counter.snapshot(20, start_unix_seconds + 20)
    assert after_midnight["http_requests_last_24h"] == 2
    assert after_midnight["http_requests_since_start"] == 2
    assert after_midnight["http_requests_since_midnight"] == 1
    assert after_midnight["http_requests_last_24h_complete"] is False
    assert after_midnight["http_requests_since_midnight_complete"] is True

    # Advance across another midnight without sending a request. The second
    # event remains inside the rolling window but belongs to the previous day.
    next_day = counter.snapshot(86410, start_unix_seconds + 86410)
    assert next_day["http_requests_last_24h"] == 1
    assert next_day["http_requests_since_start"] == 2
    assert next_day["http_requests_since_midnight"] == 0
    assert next_day["http_requests_last_24h_complete"] is True
    expired = counter.snapshot(86420, start_unix_seconds + 86420)
    assert expired["http_requests_last_24h"] == 0
    assert len(counter._events) == 0
    assert expired["http_requests_since_start"] == 2
    assert expired["http_requests_counting_since"] == after_midnight["http_requests_counting_since"]

    # Expiring all timestamp events must not reset the cumulative count.
    counter.record(86421, start_unix_seconds + 86421)
    resumed = counter.snapshot(86421, start_unix_seconds + 86421)
    assert resumed["http_requests_last_24h"] == 1
    assert resumed["http_requests_since_start"] == 3
    assert resumed["http_requests_counting_since"] == after_midnight["http_requests_counting_since"]


def test_request_totals_report_partial_coverage_and_reset_on_recreation():
    now_unix_seconds = datetime(2022, 1, 2, 12).timestamp()
    counter = RequestCounter()
    counter.record(0, now_unix_seconds)
    current = counter.snapshot(1, now_unix_seconds + 1)
    assert current["http_requests_last_24h"] == 1
    assert current["http_requests_since_start"] == 1
    assert current["http_requests_since_midnight"] == 1
    assert current["http_requests_last_24h_complete"] is False
    assert current["http_requests_since_midnight_complete"] is False
    assert datetime.fromisoformat(current["http_requests_counting_since"]).timestamp() == now_unix_seconds
    recreated = RequestCounter().snapshot(2, now_unix_seconds + 2)
    assert recreated["http_requests_last_24h"] == 0
    assert recreated["http_requests_since_start"] == 0
    assert recreated["http_requests_since_midnight"] == 0
    assert recreated["http_requests_counter_reset_reason"] == "module_started"
    assert recreated["http_requests_counting_since"] != current["http_requests_counting_since"]


@pytest.mark.parametrize("jump_seconds", [-3600, 3600])
def test_request_totals_restart_coverage_after_clock_correction(jump_seconds):
    start_unix_seconds = datetime(2022, 1, 2, 12).timestamp()
    counter = RequestCounter()
    counter.record(0, start_unix_seconds)
    current = counter.snapshot(10, start_unix_seconds + 10 + jump_seconds)
    assert current["http_requests_last_24h"] == 0
    assert current["http_requests_since_start"] == 0
    assert datetime.fromisoformat(current["http_requests_counting_since"]).timestamp() == (
        start_unix_seconds + 10 + jump_seconds)
    assert current["http_requests_since_midnight"] == 0
    assert current["http_requests_last_24h_complete"] is False
    assert current["http_requests_since_midnight_complete"] is False
    assert current["http_requests_counter_reset_reason"] == "clock_changed"


def test_request_totals_bound_memory_without_claiming_complete_history(monkeypatch):
    from modules.vehicles.nissanconnect.src import api

    monkeypatch.setattr(api, "MAX_REQUEST_COUNTER_EVENTS", 2)
    start_unix_seconds = datetime(2022, 1, 2, 12).timestamp()
    counter = RequestCounter()
    for offset_seconds in range(3):
        counter.record(offset_seconds, start_unix_seconds + offset_seconds)
    current = counter.snapshot(2, start_unix_seconds + 2)
    assert current["http_requests_last_24h"] == 1
    assert current["http_requests_since_start"] == 1
    assert current["http_requests_counter_reset_reason"] == "capacity_limit"
    assert datetime.fromisoformat(current["http_requests_counting_since"]).timestamp() == start_unix_seconds + 2
    assert current["http_requests_last_24h_complete"] is False
    assert current["http_requests_since_midnight_complete"] is False


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="System timezone switching requires POSIX")
@pytest.mark.parametrize("midnight_iso,event_iso,now_iso,rolling_count,day_count,midnight_offset", [
    ("2026-10-24T22:00:00+00:00", "2026-10-24T22:15:00+00:00", "2026-10-25T22:45:00+00:00", 0, 1, "+02:00"),
    ("2026-03-28T23:00:00+00:00", "2026-03-28T23:15:00+00:00", "2026-03-29T22:00:00+00:00", 1, 0, "+02:00"),
])
def test_request_totals_respect_short_and_long_local_days(
        monkeypatch, midnight_iso, event_iso, now_iso, rolling_count, day_count, midnight_offset):
    try:
        with monkeypatch.context() as context:
            context.setenv("TZ", "Europe/Berlin")
            time.tzset()
            start_unix_seconds = datetime.fromisoformat(midnight_iso).timestamp() - 3600
            event_unix_seconds = datetime.fromisoformat(event_iso).timestamp()
            now_unix_seconds = datetime.fromisoformat(now_iso).timestamp()
            counter = RequestCounter()
            counter.observe(0, start_unix_seconds)
            counter.record(event_unix_seconds - start_unix_seconds, event_unix_seconds)
            current = counter.snapshot(now_unix_seconds - start_unix_seconds, now_unix_seconds)
            assert current["http_requests_last_24h"] == rolling_count
            assert current["http_requests_since_start"] == 1
            assert current["http_requests_since_midnight"] == day_count
            assert current["http_requests_since_midnight_complete"] is True
            assert current["http_requests_local_midnight"].endswith("T00:00:00" + midnight_offset)
    finally:
        time.tzset()


def test_request_totals_count_login_odometer_failures_and_zero_request_backoff():
    client, transport, ticks = make_client(full_script() + [
        reply({"data": {"attributes": {"totalMileage": 12345.6}}}), reply({}, 503)])
    client._unix_seconds = lambda: MEASURED_UNIX_SECONDS + 86400 + ticks[0]
    client._request_counter = RequestCounter()
    client.fetch_battery(include_odometer=True)
    assert client.last_query["http_requests"] == 8
    assert client.last_query["http_requests_last_24h"] == 8
    assert client.last_query["http_requests_since_start"] == 8
    ticks[0] = 10
    with pytest.raises(NissanError):
        client.fetch_battery(include_odometer=True)
    assert client.last_query["http_requests"] == 1
    assert client.last_query["http_requests_last_24h"] == 9
    assert client.last_query["http_requests_since_start"] == 9
    ticks[0] = 20
    with pytest.raises(NissanError):
        client.fetch_battery(include_odometer=True)
    assert client.last_query["http_requests"] == 0
    assert client.last_query["http_requests_last_24h"] == 9
    assert client.last_query["http_requests_since_start"] == 9
    assert len(transport.calls) == 9


def test_request_totals_include_transport_failure_without_a_response():
    def fail_transport(calls):
        raise NissanError("Synthetic transport failure")

    client, _, _ = make_client([fail_transport])
    client._request_counter = RequestCounter()
    with pytest.raises(NissanError):
        client.fetch_battery()
    assert client.last_query["last_http_status"] is None
    assert client.last_query["http_requests_last_24h"] == 1
    assert client.last_query["http_requests_since_start"] == 1


def test_separate_connection_test_has_no_native_vehicle_history():
    client, _, _ = make_client(full_script() + [reply({"data": {"attributes": {"totalMileage": 0}}})])
    result = run_test({'user_id': 'synthetic@example.invalid', 'password': 'synthetic-password'},
                      client_factory=lambda *args: client)
    assert result["success"] is True
    assert result["query"]["http_requests"] == 8
    assert "http_requests_last_24h" not in result["query"]
    assert "http_requests_since_start" not in result["query"]
