"""MyNISSAN EU/OneID client. Cached battery/odometer data; no vehicle commands.

Protocol adapted from HomeAssistant-NissanConnect; see NOTICE.md for attribution.
Adapted for openWB by wippofax, 2026-09-11 through 2026-10-10, under GPLv3.
Credentials, cookies and tokens stay in memory. Never log transport payloads.
"""
import base64
from collections import deque
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
from http import HTTPStatus
from http.client import HTTPException
from http.cookiejar import CookieJar
import json
import math
import re
import secrets
import ssl
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, HTTPRedirectHandler, HTTPSHandler, Request


AUTH_BASE_URL = "https://login.mynissan-account.com/"
BFF_BASE_URL = "https://nci-bff-web-prod.apps.eu2.kamereon.io/bff-web/"
USERS_BASE_URL = "https://alliance-platform-usersadapter-prod.apps.eu2.kamereon.io/user-adapter/"
CARS_BASE_URL = "https://alliance-platform-caradapter-prod.apps.eu2.kamereon.io/car-adapter/"
OAUTH_CALLBACK_URI = "com://wso2.service.nci"
# Public application identifier from the reference implementation; not a secret.
OAUTH_CLIENT_ID = "ZM3WK7ax1OtQKYQ8Qqzcv5VgiA8a"
OAUTH_LOGIN_SCOPE = "openid name profile email offline_access"
# Transport/query limits use seconds and bytes, not decoded character counts.
MAX_RESPONSE_BYTES = 1024 * 1024
SOCKET_TIMEOUT_SECONDS = 10
QUERY_BUDGET_SECONDS = 60
MAX_MEASUREMENT_FUTURE_SKEW_SECONDS = 300
DEFAULT_HTTPS_PORT = 443
MAX_LOGIN_REDIRECTS = 10
MAX_AUTHENTICATED_REQUEST_ATTEMPTS = 2

# Keep separate policies separate even when their current values are equal.
DEFAULT_TOKEN_LIFETIME_SECONDS = 3600
TOKEN_REFRESH_MARGIN_SECONDS = 30
DEFAULT_RETRY_AFTER_SECONDS = 300
MIN_RETRY_AFTER_SECONDS = 300
MAX_RETRY_AFTER_SECONDS = 86400
INITIAL_FAILURE_BACKOFF_SECONDS = 300
MAX_FAILURE_BACKOFF_SECONDS = 3600
MAX_FAILURE_BACKOFF_STEPS = 5
FAILURE_BACKOFF_MULTIPLIER = 2
ODOMETER_FAILURE_BACKOFF_SECONDS = 300
MAX_SOC_PERCENT = 100
DURATION_DECIMAL_PLACES = 3
DATA_AGE_DECIMAL_PLACES = 1
REQUEST_COUNTER_WINDOW_SECONDS = 24 * 60 * 60
REQUEST_COUNTER_CLOCK_SKEW_SECONDS = 5
MAX_REQUEST_COUNTER_EVENTS = 100000

PKCE_VERIFIER_RANDOM_BYTES = 64
OAUTH_STATE_RANDOM_BYTES = 32
VIN_PATTERN = r"[A-HJ-NPR-Z0-9]{17}"
JSON_API_CONTENT_TYPE = "application/vnd.api+json"
OAUTH_REFRESH_SCOPE = "openid profile vehicles"
DIAGNOSTIC_SOURCE = "nissan_cached_api"
INVALID_BATTERY_VALUE_MESSAGE = "Nissan returned an invalid battery value."
INVALID_LOGIN_REDIRECT_MESSAGE = "Unexpected redirect during Nissan login."
INVALID_LOGIN_FORM_DESTINATION_MESSAGE = "Unexpected Nissan login form destination."
REDIRECT_STATUSES = (HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.FOUND, HTTPStatus.SEE_OTHER,
                     HTTPStatus.TEMPORARY_REDIRECT, HTTPStatus.PERMANENT_REDIRECT)


class RequestCounter:
    """In-memory request history owned by one native vehicle module instance.

    Store timestamps and a cumulative count, never account or vehicle identifiers.
    The cumulative count survives expiry of individual request timestamps.
    Monotonic time defines the rolling window; local calendar time defines the
    current day, which may last 23 or 25 hours. Keep an event while either window
    needs it. Resets expose a new coverage start instead of claiming a full day.
    The ordinary vehicle updater serializes access; no cross-process sharing.
    """

    def __init__(self):
        self._events = deque()
        self._requests_since_start_count = 0
        self._started_monotonic_seconds = None
        self._started_unix_seconds = None
        self._last_monotonic_seconds = None
        self._reset_reason = "module_started"

    def _reset(self, monotonic_seconds, unix_seconds, reason):
        self._events.clear()
        self._requests_since_start_count = 0
        self._started_monotonic_seconds = monotonic_seconds
        self._started_unix_seconds = unix_seconds
        self._reset_reason = reason

    def observe(self, monotonic_seconds, unix_seconds):
        """Advance coverage and expiry even when backoff sends no request."""
        if self._started_monotonic_seconds is None:
            self._reset(monotonic_seconds, unix_seconds, "module_started")
        elif (monotonic_seconds < self._last_monotonic_seconds or abs(
                (unix_seconds - self._started_unix_seconds) -
                (monotonic_seconds - self._started_monotonic_seconds)) > REQUEST_COUNTER_CLOCK_SKEW_SECONDS):
            self._reset(monotonic_seconds, unix_seconds, "clock_changed")
        self._last_monotonic_seconds = monotonic_seconds
        # A naive local midnight is converted using that date's system timezone
        # rules, not the current fixed UTC offset (which can differ after DST).
        midnight = datetime.fromtimestamp(unix_seconds).replace(hour=0, minute=0, second=0, microsecond=0, fold=0)
        midnight_unix_seconds = midnight.timestamp()
        cutoff_monotonic_seconds = monotonic_seconds - REQUEST_COUNTER_WINDOW_SECONDS
        while (self._events and self._events[0][0] <= cutoff_monotonic_seconds
               and self._events[0][1] < midnight_unix_seconds):
            self._events.popleft()
        return midnight

    def record(self, monotonic_seconds, unix_seconds):
        """Count immediately before transport, including requests that fail."""
        self.observe(monotonic_seconds, unix_seconds)
        if len(self._events) >= MAX_REQUEST_COUNTER_EVENTS:
            # Bound memory without silently truncating an allegedly complete sum.
            self._reset(monotonic_seconds, unix_seconds, "capacity_limit")
        self._events.append((monotonic_seconds, unix_seconds))
        self._requests_since_start_count += 1

    def snapshot(self, monotonic_seconds, unix_seconds):
        midnight = self.observe(monotonic_seconds, unix_seconds)
        midnight_unix_seconds = midnight.timestamp()
        cutoff_monotonic_seconds = monotonic_seconds - REQUEST_COUNTER_WINDOW_SECONDS
        return {
            "http_requests_last_24h": sum(event[0] > cutoff_monotonic_seconds for event in self._events),
            "http_requests_since_midnight": sum(event[1] >= midnight_unix_seconds for event in self._events),
            "http_requests_since_start": self._requests_since_start_count,
            "http_requests_counting_since": datetime.fromtimestamp(
                self._started_unix_seconds, timezone.utc).isoformat(),
            "http_requests_local_midnight": midnight.astimezone().isoformat(),
            "http_requests_last_24h_complete": self._started_monotonic_seconds <= cutoff_monotonic_seconds,
            "http_requests_since_midnight_complete": self._started_unix_seconds < midnight_unix_seconds,
            "http_requests_counter_reset_reason": self._reset_reason,
        }


class NissanError(Exception):
    """A deliberately bounded message safe for openWB's error reporting."""


class AuthenticationError(NissanError):
    pass


class RateLimitError(NissanError):
    pass


@dataclass
class HttpResponse:
    status: int
    headers: dict = field(repr=False)
    body: str = field(repr=False)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PrivateTransport:
    """TLS-verified transport without response logging, netrc or automatic redirects.

    openWB's standard requests hook logs complete authentication responses. urllib
    avoids that hook and urllib3's debug logging of URLs containing VINs/codes.
    CookieJar is memory-only; no cookie or token cache is written to disk.
    urllib may inherit system/environment proxies; TLS still uses the local
    trust store. This transport is not an independent network sandbox.
    """

    def __init__(self):
        self._cookies = CookieJar()
        self._opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            HTTPCookieProcessor(self._cookies), _NoRedirect())

    def clear_cookies(self):
        self._cookies.clear()

    def request(self, method, url, headers=None, form=None, json_body=None, timeout_seconds=SOCKET_TIMEOUT_SECONDS):
        request_headers = dict(headers or {})
        data = None
        if form is not None:
            data = urlencode(form).encode("utf-8")
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        elif json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            request_headers["Content-Type"] = JSON_API_CONTENT_TYPE
        try:
            request = Request(url, data=data, headers=request_headers, method=method)
            try:
                response = self._opener.open(request, timeout=timeout_seconds)
            except HTTPError as error:
                response = error
            with response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if len(body) > MAX_RESPONSE_BYTES:
                    raise NissanError("Nissan response is too large.")
                return HttpResponse(response.code, dict(response.headers), body.decode("utf-8"))
        except (URLError, OSError, HTTPException, ValueError):
            raise NissanError("Nissan is unreachable or returned an invalid response.") from None


class _LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current = {"action": attrs.get("action"), "inputs": {}}
        elif tag == "input" and self.current is not None and attrs.get("name"):
            self.current["inputs"][attrs["name"]] = attrs.get("value", "")

    def handle_endtag(self, tag):
        if tag == "form" and self.current is not None:
            self.forms.append(self.current)
            self.current = None

    @classmethod
    def parse(cls, body):
        parser = cls()
        parser.feed(body)
        for form in parser.forms:
            if {"sessionDataKey", "password"}.issubset(form["inputs"]):
                return form
        return None


def _origin(url):
    try:
        parsed = urlsplit(url)
        if parsed.username or parsed.password or parsed.fragment or parsed.scheme != "https":
            return None
        return parsed.hostname, parsed.port or DEFAULT_HTTPS_PORT
    except ValueError:
        return None


def _object(response):
    try:
        body = json.loads(response.body)
    except (ValueError, TypeError):
        raise NissanError("Nissan returned an invalid JSON response.") from None
    if not isinstance(body, dict) or body.get("errors") or body.get("error"):
        raise NissanError("Nissan reported an error or returned an unknown response format.")
    return body


def _number(value, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NissanError(INVALID_BATTERY_VALUE_MESSAGE)
    try:
        value = float(value)
    except OverflowError:
        raise NissanError(INVALID_BATTERY_VALUE_MESSAGE) from None
    if not math.isfinite(value) or value < 0 or (maximum is not None and value > maximum):
        raise NissanError(INVALID_BATTERY_VALUE_MESSAGE)
    return float(value)


@dataclass(frozen=True)
class BatteryStatus:
    """SoC and its Unix measurement time; optional range/odometer in km.

    The battery timestamp does not describe the separate cockpit odometer.
    """

    soc_percent: float
    measurement_unix_seconds: float
    range_km: Optional[float] = None
    odometer_km: Optional[float] = None


def parse_battery(body, now_unix_seconds=None):
    """Require an actual, timezone-aware measurement time; never substitute now."""
    try:
        attributes = body["data"]["attributes"]
        soc_percent = _number(attributes["batteryLevel"], MAX_SOC_PERCENT)
        raw_time = attributes["lastUpdateTime"]
        if not isinstance(raw_time, str):
            raise ValueError
        measured = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
        if measured.tzinfo is None or measured.utcoffset() is None:
            raise ValueError
        measurement_unix_seconds = measured.timestamp()
        if not math.isfinite(measurement_unix_seconds) or measurement_unix_seconds <= 0 or measurement_unix_seconds > (
                time.time() if now_unix_seconds is None else now_unix_seconds) + MAX_MEASUREMENT_FUTURE_SKEW_SECONDS:
            raise ValueError
        range_km = attributes.get("rangeHvacOn")
        if range_km is None:
            range_km = attributes.get("rangeHvacOff")
        # An unavailable optional range must not discard a valid SoC measurement.
        try:
            range_km = None if range_km is None else _number(range_km)
        except NissanError:
            range_km = None
        return BatteryStatus(soc_percent, measurement_unix_seconds, range_km)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise NissanError("Nissan did not return a valid SoC with a measurement timestamp.") from None


def parse_odometer(body):
    """Read totalMileage in km; never substitute mileage, range or zero.

    The reference OdometerSensor maps cockpit.totalMileage to kilometres. It
    supplies no odometer measurement timestamp. Missing or invalid optional
    data must not invalidate a successful battery measurement.
    """
    try:
        return _number(body["data"]["attributes"]["totalMileage"])
    except (KeyError, TypeError, NissanError):
        return None


class NissanClient:
    """Stateful client for one account/vehicle; callers must serialize its use.

    Keeps tokens, vehicle selection and backoff in memory between queries.
    Create a new instance when credentials/VIN change. The injected transport
    and clocks support synthetic tests; production requests use PrivateTransport.
    """

    def __init__(self, user_id, password, vin=None, transport=None,
                 monotonic_seconds=time.monotonic, unix_seconds=time.time, request_counter=None):
        self._user = user_id
        self._password = password
        self._configured_vin = (vin or "").strip().upper()
        self._transport = transport if transport is not None else PrivateTransport()
        self._monotonic_seconds = monotonic_seconds
        self._unix_seconds = unix_seconds
        self._request_counter = request_counter
        self._access_token = None
        self._refresh_token = None
        self._expires_at_monotonic_seconds = 0
        self._user_id = None
        self._vin = None
        self._retry_at_monotonic_seconds = 0
        self._provider_retry_at_monotonic_seconds = 0
        self._failed_queries = 0
        self._retry_error_type = NissanError
        self._retry_reason = ""
        self._deadline_monotonic_seconds = None
        self.last_query = None
        self._last_contact_unix_seconds = None
        self._last_success_unix_seconds = None
        self._last_measurement_unix_seconds = None
        self._request_started_unix_seconds = None
        self._request_count = 0
        self._http_status = None
        self._phase = "idle"
        self._odometer_retry_at_monotonic_seconds = 0
        self._odometer_outcome = "not_requested"
        self._odometer_http_status = None
        self._odometer_received_unix_seconds = None

    def _request(self, method, url, auth_request=False, **kwargs):
        if _origin(url) not in {_origin(AUTH_BASE_URL), _origin(BFF_BASE_URL),
                                _origin(USERS_BASE_URL), _origin(CARS_BASE_URL)}:
            raise NissanError("Unexpected Nissan request destination; request aborted.")
        remaining_seconds = self._deadline_monotonic_seconds - self._monotonic_seconds()
        if remaining_seconds <= 0:
            raise NissanError("Nissan query time limit exceeded.")
        self._last_contact_unix_seconds = self._unix_seconds()
        if self._request_started_unix_seconds is None:
            self._request_started_unix_seconds = self._last_contact_unix_seconds
        self._request_count += 1
        if self._request_counter is not None:
            self._request_counter.record(self._monotonic_seconds(), self._last_contact_unix_seconds)
        self._http_status = None
        response = self._transport.request(method, url, timeout_seconds=min(
            SOCKET_TIMEOUT_SECONDS, remaining_seconds), **kwargs)
        self._http_status = response.status
        if response.status in (HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.SERVICE_UNAVAILABLE):
            self._retry_at_monotonic_seconds = self._monotonic_seconds() + self._retry_after(response)
            # Separate provider advice from the scheduled client's own error backoff.
            provider_delay_seconds = self._retry_after(
                response, minimum_seconds=0,
                default_seconds=(DEFAULT_RETRY_AFTER_SECONDS
                                 if response.status == HTTPStatus.TOO_MANY_REQUESTS else 0))
            self._provider_retry_at_monotonic_seconds = self._monotonic_seconds() + provider_delay_seconds
        if response.status == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError("Nissan is rate limiting requests. Please try again later.")
        if response.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN) or (
                auth_request and response.status == HTTPStatus.BAD_REQUEST):
            raise AuthenticationError("Nissan rejected the login or access authorization.")
        if response.status >= HTTPStatus.BAD_REQUEST:
            raise NissanError("Nissan service returned an HTTP error ({}).".format(response.status))
        return response

    def _retry_after(self, response, minimum_seconds=MIN_RETRY_AFTER_SECONDS,
                     default_seconds=DEFAULT_RETRY_AFTER_SECONDS):
        """Accept delay seconds or an HTTP date; bound server-directed pauses."""
        value = next((v for k, v in response.headers.items() if k.lower() == "retry-after"), None)
        try:
            delay_seconds = int(value)
        except (ValueError, TypeError, OverflowError):
            try:
                retry_at_datetime = parsedate_to_datetime(value)
                if retry_at_datetime.tzinfo is None:
                    raise ValueError
                delay_seconds = retry_at_datetime.timestamp() - self._unix_seconds()
            except (ValueError, TypeError, AttributeError, OverflowError):
                delay_seconds = default_seconds
        return max(minimum_seconds, min(delay_seconds, MAX_RETRY_AFTER_SECONDS))

    def _json(self, method, url, **kwargs):
        response = self._request(method, url, **kwargs)
        if not HTTPStatus.OK <= response.status < HTTPStatus.MULTIPLE_CHOICES:
            raise NissanError("Unexpected redirect from the Nissan API.")
        return _object(response)

    def _redirects(self, response, url, callback=False):
        for _ in range(MAX_LOGIN_REDIRECTS):
            if response.status not in REDIRECT_STATUSES:
                return response, url
            location = next((v for k, v in response.headers.items() if k.lower() == "location"), None)
            if not isinstance(location, str) or not location:
                break
            try:
                target = urljoin(url, location)
                parsed = urlsplit(target)
            except ValueError:
                raise NissanError(INVALID_LOGIN_REDIRECT_MESSAGE) from None
            expected = urlsplit(OAUTH_CALLBACK_URI)
            if callback and (parsed.scheme, parsed.netloc, parsed.path) == (
                    expected.scheme, expected.netloc, expected.path) and not parsed.fragment:
                return response, target
            if _origin(target) != _origin(AUTH_BASE_URL):
                raise NissanError(INVALID_LOGIN_REDIRECT_MESSAGE)
            response = self._request("GET", target)
            url = target
        raise NissanError("Too many or invalid Nissan redirects.")

    def _login(self):
        if (not isinstance(self._user, str) or not self._user.strip()
                or not isinstance(self._password, str) or not self._password):
            raise AuthenticationError("MyNISSAN username and password are required.")
        # A new login must not reuse an expired/partially authenticated web session.
        if hasattr(self._transport, "clear_cookies"):
            self._transport.clear_cookies()
        self._refresh_token = None
        verifier = secrets.token_urlsafe(PKCE_VERIFIER_RANDOM_BYTES)
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        state = secrets.token_urlsafe(OAUTH_STATE_RANDOM_BYTES)
        url = AUTH_BASE_URL + "oauth2/authorize?" + urlencode({
            "response_type": "code", "redirect_uri": OAUTH_CALLBACK_URI, "client_id": OAUTH_CLIENT_ID,
            "state": state, "scope": OAUTH_LOGIN_SCOPE, "code_challenge": challenge, "code_challenge_method": "S256",
            "locale": "en_GB", "brand": "Nissan", "client": "mynissanapp"})
        response, url = self._redirects(self._request("GET", url), url)
        form = _LoginForm.parse(response.body)
        if not form or not form["action"]:
            raise NissanError("Nissan login form is unavailable; you may need to sign in through the app.")
        try:
            target = urljoin(url, form["action"])
        except ValueError:
            raise NissanError(INVALID_LOGIN_FORM_DESTINATION_MESSAGE) from None
        if _origin(target) != _origin(AUTH_BASE_URL):
            raise NissanError(INVALID_LOGIN_FORM_DESTINATION_MESSAGE)
        data = dict(form["inputs"])
        region = data.get("regionCode", "")
        data.update(userName=self._user, username=region + "/" + self._user if region else self._user,
                    password=self._password)
        response = self._request("POST", target, form=data, headers={
                                 "Origin": AUTH_BASE_URL.rstrip("/"), "Referer": url})
        response, callback = self._redirects(response, target, callback=True)
        parsed = urlsplit(callback)
        expected = urlsplit(OAUTH_CALLBACK_URI)
        if (parsed.scheme, parsed.netloc, parsed.path) != (expected.scheme, expected.netloc, expected.path):
            raise AuthenticationError(
                "Nissan login did not complete. Check your credentials and any notices in MyNISSAN.")
        values = parse_qs(parsed.query)
        if values.get("state") != [state] or len(values.get("code", [])) != 1 or values.get("error"):
            raise AuthenticationError("Nissan returned an invalid login confirmation.")
        token = self._json("POST", AUTH_BASE_URL + "oauth2/token", auth_request=True, form={
            "grant_type": "authorization_code", "redirect_uri": OAUTH_CALLBACK_URI, "client_id": OAUTH_CLIENT_ID,
            "code": values["code"][0], "code_verifier": verifier, "scope": OAUTH_LOGIN_SCOPE})
        identity_token = token.get("id_token")
        if not isinstance(identity_token, str) or not identity_token:
            raise AuthenticationError("Nissan did not return an identity token.")
        self._install(self._json("POST", BFF_BASE_URL + "v1/oauth2/access_token?platform=Android", auth_request=True,
                                 headers={"Authorization": identity_token, "Content-Type": JSON_API_CONTENT_TYPE}))

    def _install(self, token):
        access = token.get("access_token")
        refresh = token.get("refresh_token")
        if not isinstance(access, str) or not access or (refresh is not None and not isinstance(refresh, str)):
            raise AuthenticationError("Nissan did not return a valid access token.")
        try:
            expires_in_seconds = float(token.get("expires_in", DEFAULT_TOKEN_LIFETIME_SECONDS))
            if not math.isfinite(expires_in_seconds) or expires_in_seconds <= 0:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            raise AuthenticationError("Nissan returned an invalid token lifetime.") from None
        self._access_token = access
        self._refresh_token = refresh or self._refresh_token
        self._expires_at_monotonic_seconds = (
            self._monotonic_seconds() + max(0, expires_in_seconds - TOKEN_REFRESH_MARGIN_SECONDS))

    def _authenticate(self, force=False):
        if self._access_token and not force and self._monotonic_seconds() < self._expires_at_monotonic_seconds:
            return
        if self._refresh_token:
            try:
                self._install(self._json("POST", BFF_BASE_URL + "v1/oauth2/refresh-token?platform=Android",
                                         auth_request=True,
                                         headers={"Authorization": self._refresh_token},
                                         json_body={"scope": OAUTH_REFRESH_SCOPE}))
                return
            except AuthenticationError:
                self._access_token = self._refresh_token = None
        self._login()

    def _get(self, url):
        for attempt in range(MAX_AUTHENTICATED_REQUEST_ATTEMPTS):
            try:
                return self._json("GET", url, headers={
                    "Authorization": "Bearer " + self._access_token, "Content-Type": JSON_API_CONTENT_TYPE})
            except AuthenticationError:
                if attempt:
                    raise
                self._authenticate(force=True)

    def _select_vehicle(self):
        if self._configured_vin and not re.fullmatch(VIN_PATTERN, self._configured_vin):
            raise NissanError("The configured VIN is invalid.")
        if not self._user_id:
            user = self._get(USERS_BASE_URL + "v1/users/current").get("userId")
            if not isinstance(user, str) or not user:
                raise NissanError("Nissan did not return a user identifier.")
            self._user_id = user
        vehicles = self._get(BFF_BASE_URL + "v5/users/" + quote(self._user_id, safe="") + "/cars").get("data")
        if not isinstance(vehicles, list):
            raise NissanError("Nissan did not return a vehicle list.")
        candidates = [v.get("vin", "").upper() for v in vehicles
                      if isinstance(v, dict) and isinstance(v.get("vin"), str)
                      and re.fullmatch(VIN_PATTERN, v["vin"].upper())]
        if self._configured_vin:
            if self._configured_vin not in candidates:
                raise NissanError("The configured VIN was not found in the Nissan account.")
            self._vin = self._configured_vin
        elif len(set(candidates)) == 1:
            self._vin = candidates[0]
        else:
            raise NissanError("Could not select a unique vehicle. Please configure the VIN.")

    def _optional_odometer(self):
        """Try one passive GET after battery success, within the same budget.

        Endpoint/auth/transport failures pause this optional endpoint for five
        minutes without discarding SoC or retrying login. Explicit provider
        pauses still govern subsequent queries, including battery queries.
        Never reuse an old odometer as if it came from this response.
        """
        if self._monotonic_seconds() < self._odometer_retry_at_monotonic_seconds:
            self._odometer_outcome = "deferred"
            return None
        self._phase = "odometer"
        self._http_status = None
        try:
            body = self._json("GET", CARS_BASE_URL + "v1/cars/" + self._vin + "/cockpit", headers={
                "Authorization": "Bearer " + self._access_token, "Content-Type": JSON_API_CONTENT_TYPE})
            odometer_km = parse_odometer(body)
            self._odometer_outcome = "success" if odometer_km is not None else "unavailable"
            if odometer_km is not None:
                self._odometer_received_unix_seconds = self._unix_seconds()
            return odometer_km
        except NissanError as error:
            self._odometer_outcome = "failed"
            self._odometer_retry_at_monotonic_seconds = self._monotonic_seconds() + ODOMETER_FAILURE_BACKOFF_SECONDS
            if (isinstance(error, RateLimitError)
                    or self._provider_retry_at_monotonic_seconds > self._monotonic_seconds()):
                self._retry_error_type = type(error)
                self._retry_reason = "Nissan requested a pause after the optional odometer query."
            else:
                # A cockpit-only outage must not suppress the next battery query.
                self._retry_at_monotonic_seconds = 0
            return None
        finally:
            self._odometer_http_status = self._http_status

    def _finish_query(self, outcome, started_monotonic_seconds, result=None):
        """Keep an allowlisted diagnostic summary, never raw transport data."""
        completed_unix_seconds = self._unix_seconds()
        if result is not None:
            self._last_success_unix_seconds = completed_unix_seconds
            self._last_measurement_unix_seconds = result.measurement_unix_seconds

        def iso(unix_seconds):
            return None if unix_seconds is None else datetime.fromtimestamp(unix_seconds, timezone.utc).isoformat()

        self.last_query = {
            "outcome": outcome,
            "phase": self._phase,
            "request_started_at": iso(self._request_started_unix_seconds),
            "completed_at": iso(completed_unix_seconds),
            "duration_seconds": (
                round(max(0, self._monotonic_seconds() - started_monotonic_seconds), DURATION_DECIMAL_PLACES)
            ),
            "http_requests": self._request_count,
            "last_http_status": self._http_status,
            "last_contact_at": iso(self._last_contact_unix_seconds),
            "last_success_at": iso(self._last_success_unix_seconds),
            "last_measurement_at": iso(self._last_measurement_unix_seconds),
            "measurement_at": iso(result.measurement_unix_seconds) if result else None,
            "data_age_seconds": (
                round(completed_unix_seconds - result.measurement_unix_seconds,
                      DATA_AGE_DECIMAL_PLACES) if result else None
            ),
            "soc": result.soc_percent if result else None,
            "range_km": result.range_km if result else None,
            "odometer_km": result.odometer_km if result else None,
            "odometer_outcome": self._odometer_outcome,
            "odometer_http_status": self._odometer_http_status,
            "odometer_retry_after_seconds": (
                max(0, math.ceil(self._odometer_retry_at_monotonic_seconds - self._monotonic_seconds()))
            ),
            "odometer_received_at": iso(self._odometer_received_unix_seconds),
            "retry_after_seconds": max(0, math.ceil(self._retry_at_monotonic_seconds - self._monotonic_seconds())),
            "provider_retry_after_seconds": (
                max(0, math.ceil(self._provider_retry_at_monotonic_seconds - self._monotonic_seconds()))
            ),
            "source": DIAGNOSTIC_SOURCE,
        }
        if self._request_counter is not None:
            self.last_query.update(self._request_counter.snapshot(self._monotonic_seconds(), completed_unix_seconds))

    def fetch_battery(self, include_odometer=False):
        """Return cached battery data or raise NissanError; never issue wake commands.

        Updates last_query with allowlisted diagnostics on success/failure and
        deferred calls. Failure pauses subsequent calls without sleeping. The
        60-second budget limits new request starts, not total socket read time.
        Core, not this client, decides whether to accept a measurement timestamp.
        include_odometer adds one best-effort cockpit GET after battery success;
        callers serving openWB and private tests enable it explicitly.
        """
        started_monotonic_seconds = self._monotonic_seconds()
        if self._request_counter is not None:
            self._request_counter.observe(started_monotonic_seconds, self._unix_seconds())
        self._request_started_unix_seconds = None
        self._request_count = 0
        self._http_status = None
        self._phase = "idle"
        self._odometer_outcome = "not_requested"
        self._odometer_http_status = None
        self._odometer_received_unix_seconds = None
        if started_monotonic_seconds < self._retry_at_monotonic_seconds:
            remaining_seconds = math.ceil(self._retry_at_monotonic_seconds - started_monotonic_seconds)
            self._finish_query("deferred", started_monotonic_seconds)
            raise self._retry_error_type(
                "Nissan requests are paused for {} more seconds. {}".format(remaining_seconds, self._retry_reason))
        self._deadline_monotonic_seconds = started_monotonic_seconds + QUERY_BUDGET_SECONDS
        result = None
        outcome = "failed"
        try:
            self._phase = "authentication"
            self._authenticate()
            if not self._vin:
                self._phase = "vehicle_selection"
                self._select_vehicle()
            self._phase = "battery"
            body = self._get(CARS_BASE_URL + "v1/cars/" + self._vin + "/battery-status")
            result = parse_battery(body, now_unix_seconds=self._unix_seconds())
            self._failed_queries = 0
            self._retry_at_monotonic_seconds = 0
            self._provider_retry_at_monotonic_seconds = 0
            self._retry_error_type = NissanError
            self._retry_reason = ""
            if include_odometer:
                result = replace(result, odometer_km=self._optional_odometer())
            outcome = "success"
            return result
        except NissanError as error:
            if isinstance(error, AuthenticationError):
                self._access_token = self._refresh_token = None
                self._user_id = self._vin = None
            # Do not sleep in an openWB worker or retain exception tracebacks.
            # A successful query resets this backoff; deferred calls do not extend it.
            self._failed_queries = min(self._failed_queries + 1, MAX_FAILURE_BACKOFF_STEPS)
            delay_seconds = min(
                INITIAL_FAILURE_BACKOFF_SECONDS * FAILURE_BACKOFF_MULTIPLIER ** (self._failed_queries - 1),
                MAX_FAILURE_BACKOFF_SECONDS)
            self._retry_at_monotonic_seconds = max(
                self._retry_at_monotonic_seconds, self._monotonic_seconds() + delay_seconds)
            self._retry_error_type = type(error)
            self._retry_reason = str(error)
            raise
        finally:
            self._deadline_monotonic_seconds = None
            self._finish_query(outcome, started_monotonic_seconds, result)
