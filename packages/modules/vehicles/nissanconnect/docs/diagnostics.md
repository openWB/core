# Query diagnostics, errors and connection tests

## Requests, measurements and scheduling

The module reads cached Nissan data; it sends no wakeup, refresh or charging
commands. Core calls the updater according to its ordinary vehicle settings
or a manual SoC refresh. A scheduled invocation can be deferred by client
backoff without making an HTTP request.

In the inspected openWB 2.2.3 Core (`3ced7f9cef3c70980ee1fab670f0d0717d1809ca`):

- Status displays `soc_timestamp`, set from Nissan's battery measurement time.
  It need not change after a successful query and is independent of percentage changes.
- `soc_request_timestamp` records a Core updater attempt, not proof of an HTTP request.
- Switching modules does not reset that request timestamp or force an immediate
  query. Normal scheduling applies the currently saved interval to it.
- Manual refresh bypasses the scheduler interval, but not the client's retry
  delay or Core's measurement timestamp guard.
- Core rejects a measurement more than 60 seconds older than its stored value,
  logging `Not updating SoC, because timestamp is older.` at DEBUG. A recent
  manual value can therefore remain visible after successful Nissan retrieval.

These source-level behaviors do not identify the cause of a particular private
trial. Later Core versions may differ; the module does not replace these policies.

## Scheduled-query diagnostics

Each updater invocation emits one JSON summary at DEBUG through the existing
SoC logger (`soc.log` when that context permits DEBUG). The standalone probe
and settings worker do not write these scheduled-query records.

| Fields | Meaning |
| --- | --- |
| `outcome`, `phase` | Success, failure or deferred invocation; current query phase |
| `request_started_at` | First actual HTTP attempt in this invocation; null when deferred |
| `completed_at`, `duration_seconds` | Completion time and elapsed monotonic seconds |
| `http_requests`, `last_http_status` | HTTP attempts in this invocation (including login/token requests and failed attempts), and latest response status if available |
| `http_requests_last_24h` | Request attempts in the rolling preceding 24 hours, for this vehicle module instance |
| `http_requests_since_midnight` | Request attempts since 00:00 in the wallbox's local timezone, for this vehicle module instance |
| `http_requests_since_start` | Total request attempts since `http_requests_counting_since`, including attempts older than 24 hours |
| `http_requests_counting_since` | UTC timestamp at which the current counting period started |
| `http_requests_local_midnight` | Current day's local midnight, including its UTC offset |
| `http_requests_last_24h_complete`, `http_requests_since_midnight_complete` | Whether observation covers the entire respective window |
| `http_requests_counter_reset_reason` | Why the current observation period started: `module_started`, `clock_changed` or `capacity_limit` |
| `last_contact_at` | Latest actual HTTP attempt, including failures; retained during backoff |
| `last_success_at` | Latest successful battery query, retained after failure |
| `measurement_at`, `data_age_seconds` | Original battery measurement and its age at completion |
| `last_measurement_at` | Measurement time from the latest successful battery query |
| `soc`, `range_km` | Parsed battery percentage and optional range; null without valid battery data |
| `odometer_km`, `odometer_outcome` | Total kilometres when available and success/unavailable/failed/deferred/not_requested status |
| `odometer_http_status`, `odometer_retry_after_seconds` | Odometer endpoint status when available and remaining separate pause |
| `odometer_received_at` | Reception time of a valid odometer; its measurement time is unknown |
| `retry_after_seconds` | Remaining client pause |
| `provider_retry_after_seconds` | Remaining provider advice, excluding the client's own error backoff |
| `source` | `nissan_cached_api` |

Times are ISO 8601 UTC, except `http_requests_local_midnight`, which includes
the wallbox-local UTC offset. A deferred invocation has zero HTTP requests and no new
request start. A small negative data age can indicate clock skew. `outcome=success`
means the client retrieved valid battery data, before Core decides whether to
accept the returned state. Odometer reception time never substitutes for battery
or odometer measurement time.

Module summaries exclude usernames, passwords, VINs, tokens, cookies, URLs, raw
responses and transport exceptions. Vehicle values and times remain private;
see the separate [inherited logging limitation](privacy.md#logs-and-retention).

## Rolling and daily request totals

Search scheduled SoC DEBUG logs for `http_requests_last_24h` and
`http_requests_since_midnight`; `http_requests_since_start` gives the cumulative
total since the timestamp in `http_requests_counting_since`. This total keeps
growing across midnights and when requests expire from the rolling window.
The totals count each HTTP attempt immediately
before transport, including login, token renewal, vehicle selection, battery,
odometer and failed attempts. A paused invocation adds no request. An attempt is
not proof that the server received it. Totals are updated even while DEBUG is
disabled and are reported when the next updater invocation is logged.

History belongs to one configured vehicle's module instance. Automatic updates
and the normal manual SoC refresh share it; a replacement API client within that
instance keeps the history. Other vehicles, the MyNISSAN app, private probes and
the separately executed settings connection tests are excluded. These are not
account-wide provider statistics; the settings test still shows only its own
`http_requests` count.

Request timestamps and a cumulative count are retained in memory; no new file
or MQTT topic is created. Restarting or recreating the vehicle module resets
history and the cumulative count together with their start timestamp. The
`http_requests_counting_since` value identifies the observed period and each
`*_complete` flag remains false until its full window has been observed. A zero
with incomplete coverage is not a claim that no earlier requests occurred.

The rolling window uses elapsed monotonic seconds and excludes events exactly
24 hours old. The daily window starts at local midnight, including on 23-hour
and 25-hour days. A system-clock correction exceeding five seconds or a backward
monotonic clock starts a new observation period. A 100,000-event memory bound
also resets coverage explicitly instead of silently dropping counted history.
Each reset restarts the cumulative count and its start timestamp together.
The reset reason remains visible. These diagnostics do not change polling,
backoff, charging control or Nissan rate limits.

## Validation, retries and Core fallback

SoC must be finite and within 0–100%; a genuine zero is valid. Battery time must
include a timezone, be positive and be no more than five minutes ahead of the
local clock. Invalid required fields fail; missing or invalid range/odometer
values remain unavailable rather than being fabricated or copied from an earlier
response. Their absence does not invalidate a valid battery result.

The transport verifies HTTPS certificates, restricts destinations and redirects,
and limits each response to 1 MiB. Socket timeouts are at most ten seconds;
no new request starts after a 60-second query budget. This is not a hard deadline
for a socket operation already running. Tokens are reused in memory; changing
account configuration or restarting the module creates a new client.

Failed battery queries use pauses of 5, 10, 20, 40 and then at most 60 minutes.
Success resets that sequence. HTTP 429/503 honor `Retry-After` in seconds or
HTTP-date form, bounded to 5 minutes through 24 hours for the scheduled client.
Deferred invocations make no HTTP request and do not extend the pause. Actual
retry time also depends on Core's polling interval. Authorization failure clears
rejected tokens; ordinary service/network failures retain authentication for reuse.

After valid battery data, the module automatically attempts to read
`totalMileage` from the cockpit endpoint using the same token and request budget,
subject to retry pauses. Users do not need to enable a separate odometer option.
Only data availability is conditional: unavailable or invalid mileage and query
errors leave the successful battery result usable. Odometer endpoint errors pause
that endpoint for five minutes without forcing a second login. Provider rate-limit
advice can also defer subsequent requests.

The existing Core wrapper may calculate SoC from metered charging energy after
failed or stale API data when its required inputs are available. This depends on
connection state, previous SoC, meter readings, battery capacity and efficiency;
the pinned fallback also treats a previous zero SoC as absent. If fallback fails,
normal Core fault handling applies. In the pinned version, three consecutive
failed updates lead to publication of zero before the next update; deferred
client calls can count as failed updates without being HTTP requests. Zero does
not mean unknown to the charge-limit logic, so an API failure does not guarantee
charging stops at the intended SoC target. The module neither suppresses errors
nor changes that policy, and exposes no separate `calculate_soc` setting.

## Settings connection test

**Test connection** uses current form values without saving them or publishing
results to MQTT/charging control. It displays selected battery/odometer values,
query times, original battery time and battery data age in the browser's timezone.
The result also shows **Nissan HTTP requests (this test)** from `http_requests`,
including authentication, vehicle selection, battery and odometer attempts.
Failed attempts count too; this is not proof that Nissan received every request.
The count is shown on success and failure when available. Missing or invalid
counts and interrupted responses show **Not available**, never an assumed zero.
This is a per-test count, not a persistent total across tests or scheduled queries.
Displaying it triggers no additional Nissan requests.

Changing input clears the result. An in-flight result from the previous input
is discarded, while any resulting cooldown remains associated with its account.

The settings build delivers both PHP files from `public/modules/vehicles/nissanconnect/`.
The endpoint URL is `/openWB/web/settings/modules/vehicles/nissanconnect/test_connection.php`;
it invokes Core's `packages/modules/vehicles/nissanconnect/connection_test.py`.
Production requires Linux, PHP 7.4+ with `proc_open` and Python 3.9+ at
`/usr/bin/python3`. UI-only installation cannot supply the Python worker.

The endpoint accepts same-origin JSON POST and inherits web-server access control.
Origin checks are not authentication; reverse proxies must preserve the actual
scheme/host relationship. Credentials go through POST and worker stdin, never
command arguments. Responses use `no-store`, stderr is discarded and errors use
fixed codes. Run actual account tests privately; the agent-environment guard is
only a precaution. See [privacy](privacy.md) for storage and transport boundaries.

Only one settings test runs at a time. Complete battery success, including zero
SoC, starts a five-minute account cooldown at completion. Account changes are
allowed; returning to an account retains its pause, even with changed password
or VIN. Ordinary failure or a busy response adds no account cooldown. Provider
advice is independent and applies across accounts when its scope is unknown:
429 without usable advice defaults to five minutes; valid 429/503 advice is
capped at 24 hours; 503 without usable advice adds no manual-test pause.

The server stores account cooldown digests and expiry times in private temporary
state. It remains authoritative after a reload or across browser tabs. This
manual-test state is separate from scheduled-client authentication and backoff.
The PHP parent terminates a still-running worker after 70 seconds; the browser
times out after 75 seconds. Closing the page does not guarantee cancellation of
a server query already running. These limits are covered by synthetic tests;
they do not prove every target host's process behavior.

## Color-theme refresh indicator

In the inspected 2.2.3 Color theme, the pending indicator clears only when the
connected-vehicle SoC object is republished with changed contents. Cached data
or a rejected older measurement can leave it pending after the query finishes.
A change in percentage, time, range or fault data can trigger that publication;
the percentage alone is not decisive. The theme has no timeout for this flag.
Reloading resets the local indicator, not vehicle measurements. This separate
theme behavior is not worked around by inventing times or publishing chargepoint
state from the Nissan module.
