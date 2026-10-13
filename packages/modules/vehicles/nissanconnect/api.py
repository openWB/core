"""Passive MyNISSAN EU client; tested with Leaf ZE1. No vehicle commands.

Adapted by wippofax from dan-r/HomeAssistant-NissanConnect, revision
b0bafe9108d4574e243aa182324584dbc68369ad (MIT), kamereon/kamereon.py.
Upstream credits @mitchellrj and @Tobiaswk; Apache-2.0 portions relicensed with permission.
https://github.com/dan-r/HomeAssistant-NissanConnect
"""
# MIT License -- Copyright (c) 2024 Daniel Raper
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import base64
from contextvars import ContextVar
from datetime import datetime
import hashlib
from html.parser import HTMLParser
from http import HTTPStatus
import logging
import math
import re
import secrets
import time
from typing import Optional, Tuple
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlsplit

from requests import ConnectionError, RequestException, Timeout
from requests.exceptions import SSLError
from modules.common.req import get_http_session

log = logging.getLogger(__name__)
AUTH_BASE_URL = "https://login.mynissan-account.com/"
BFF_BASE_URL = "https://nci-bff-web-prod.apps.eu2.kamereon.io/bff-web/"
USERS_BASE_URL = "https://alliance-platform-usersadapter-prod.apps.eu2.kamereon.io/user-adapter/"
CARS_BASE_URL = "https://alliance-platform-caradapter-prod.apps.eu2.kamereon.io/car-adapter/"
OAUTH_CALLBACK_URI = "com://wso2.service.nci"
OAUTH_CLIENT_ID = "ZM3WK7ax1OtQKYQ8Qqzcv5VgiA8a"  # Public application identifier, not a secret.
OAUTH_LOGIN_SCOPE = "openid name profile email offline_access"
JSON_API_CONTENT_TYPE = "application/vnd.api+json"
REQUEST_TIMEOUT_SECONDS = 10
DEFAULT_TOKEN_LIFETIME_SECONDS = 3600
TOKEN_REFRESH_MARGIN_SECONDS = 30
MAX_MEASUREMENT_FUTURE_SKEW_SECONDS = 300
MAX_SOC_PERCENT = 100
FULL_BATTERY_BAR_UNITS = 240
MAX_SOC_DIFFERENCE_PERCENT_POINTS = 1
MAX_LOGIN_REDIRECTS = 10
PKCE_VERIFIER_RANDOM_BYTES = 64
OAUTH_STATE_RANDOM_BYTES = 32
VIN_PATTERN = r"[A-HJ-NPR-Z0-9]{17}"
_PRIVATE_HTTP_REQUEST = ContextVar("nissan_private_http_request", default=False)


def _allow_transport_log(record):
    """Suppress URL/payload diagnostics only inside this context's Nissan HTTP calls."""
    return not _PRIVATE_HTTP_REQUEST.get()


# Parent logger filters do not cover child records; register once on the emitters.
for _logger_name in ("urllib3.connection", "urllib3.connectionpool", "urllib3.poolmanager",
                     "urllib3.response", "urllib3.util.retry"):
    logging.getLogger(_logger_name).addFilter(_allow_transport_log)


class NissanError(Exception):
    """Errors omit response bodies, credentials and account identifiers."""


class AuthenticationError(NissanError):
    pass


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


def _login_target(url):
    """Only follow HTTPS login redirects and submit credentials to the login host."""
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != urlsplit(AUTH_BASE_URL).netloc or parsed.fragment):
        raise NissanError("Unexpected Nissan login destination.")
    return url


def _number(value, maximum=math.inf):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value < math.inf or value > maximum:
        raise NissanError("Nissan returned an invalid vehicle measurement.")
    try:
        return float(value)
    except OverflowError:
        raise NissanError("Nissan returned an invalid vehicle measurement.") from None


def _soc_percent(attributes):
    """Prefer the Leaf's finer 0-240 scale when it agrees with the required percent value."""
    soc_percent = _number(attributes["batteryLevel"], MAX_SOC_PERCENT)
    try:
        bar_units = _number(attributes.get("batteryBarLevel"), FULL_BATTERY_BAR_UNITS)
    except NissanError:
        return soc_percent
    bar_soc_percent = bar_units / FULL_BATTERY_BAR_UNITS * MAX_SOC_PERCENT
    # Allow integer-percent quantization, but reject a zero placeholder for a positive SoC.
    if ((bar_units > 0 or soc_percent == 0)
            and abs(bar_soc_percent - soc_percent) <= MAX_SOC_DIFFERENCE_PERCENT_POINTS):
        return bar_soc_percent
    return soc_percent


def parse_battery(body) -> Tuple[float, Optional[float], float]:
    """Preserve the actual measurement time and valid zero values; never invent a SoC."""
    try:
        attributes = body["data"]["attributes"]
        soc_percent = _soc_percent(attributes)
        measured = datetime.fromisoformat(attributes["lastUpdateTime"].replace("Z", "+00:00"))
        measurement_unix_seconds = measured.timestamp()
        if (measured.tzinfo is None
                or not 0 < measurement_unix_seconds <= time.time() + MAX_MEASUREMENT_FUTURE_SKEW_SECONDS):
            raise ValueError
        range_km = attributes.get("rangeHvacOn")
        if range_km is None:
            range_km = attributes.get("rangeHvacOff")
        try:
            range_km = _number(range_km)
        except NissanError:
            range_km = None
        return soc_percent, range_km, measurement_unix_seconds
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise NissanError("Nissan did not return a valid SoC with a measurement timestamp.") from None


class NissanClient:
    def __init__(self, user_id, password, vin=None):
        self._user = user_id
        self._password = password
        self._configured_vin = (vin or "").strip().upper()
        self._vin = None
        self._access_token = self._refresh_token = None
        self._expires_at_monotonic_seconds = 0
        self._session = get_http_session()
        # The shared response hook logs full tokens/payloads. Check status locally instead.
        self._session.hooks["response"] = []
        self._session.trust_env = False  # Do not load unrelated netrc credentials or proxies.

    def _request(self, method, url, auth_request=False, **kwargs):
        log_context = _PRIVATE_HTTP_REQUEST.set(True)
        try:
            response = self._session.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS,
                                             allow_redirects=False, **kwargs)
        except Timeout:
            raise NissanError("Nissan request timed out.") from None
        except SSLError:
            raise NissanError("Nissan TLS connection failed.") from None
        except ConnectionError:
            raise NissanError("Nissan connection failed.") from None
        except RequestException:
            raise NissanError("Nissan could not be reached.") from None
        finally:
            _PRIVATE_HTTP_REQUEST.reset(log_context)
        if response.status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN) or (
                auth_request and response.status_code == HTTPStatus.BAD_REQUEST):
            raise AuthenticationError("Nissan rejected the login or access authorization.")
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise NissanError(f"Nissan service returned HTTP {response.status_code}.")
        return response

    def _json(self, method, url, **kwargs):
        response = self._request(method, url, **kwargs)
        try:
            body = response.json()
            if not isinstance(body, dict) or body.get("error") or body.get("errors"):
                raise ValueError
            return body
        except ValueError:
            raise NissanError("Nissan returned an invalid response.") from None

    def _redirects(self, response, url, callback=False):
        for _ in range(MAX_LOGIN_REDIRECTS):
            if not response.is_redirect:
                return response, url
            target = urljoin(url, response.headers["Location"])
            if callback and target.split("?", 1)[0] == OAUTH_CALLBACK_URI:
                return response, target
            url = _login_target(target)
            response = self._request("GET", url)
        raise NissanError("Too many Nissan login redirects.")

    def _login(self):
        """Sign in through MyNISSAN, then exchange its identity token for Nissan API tokens."""
        if not self._user or not self._password:
            raise AuthenticationError("MyNISSAN username and password are required.")
        self._session.cookies.clear()
        self._access_token = self._refresh_token = None
        # Request a PKCE-bound authorization code through the hosted login form.
        verifier = secrets.token_urlsafe(PKCE_VERIFIER_RANDOM_BYTES)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(OAUTH_STATE_RANDOM_BYTES)
        url = AUTH_BASE_URL + "oauth2/authorize?" + urlencode({
            "response_type": "code", "redirect_uri": OAUTH_CALLBACK_URI, "client_id": OAUTH_CLIENT_ID,
            "state": state, "scope": OAUTH_LOGIN_SCOPE, "code_challenge": challenge, "code_challenge_method": "S256",
            "locale": "en_GB", "brand": "Nissan", "client": "mynissanapp"})
        response, url = self._redirects(self._request("GET", url), url)
        parser = _LoginForm()
        parser.feed(response.text)
        form = next((f for f in parser.forms if {"sessionDataKey", "password"}.issubset(f["inputs"])), None)
        if not form or not form["action"]:
            raise AuthenticationError("Nissan login form is unavailable. Check sign-in through MyNISSAN.")
        target = _login_target(urljoin(url, form["action"]))
        data = form["inputs"]
        region = data.get("regionCode", "")
        data.update(userName=self._user, username=region + "/" + self._user if region else self._user,
                    password=self._password)
        response = self._request("POST", target, data=data, headers={
            "Origin": AUTH_BASE_URL.rstrip("/"), "Referer": url})
        _, callback = self._redirects(response, target, callback=True)
        values = parse_qs(urlsplit(callback).query)
        if (callback.split("?", 1)[0] != OAUTH_CALLBACK_URI or urlsplit(callback).fragment
                or values.get("state") != [state] or len(values.get("code", [])) != 1 or values.get("error")):
            raise AuthenticationError("Nissan login did not complete. Check credentials and notices in MyNISSAN.")
        # Redeem the authorization code at the identity provider.
        token = self._json("POST", AUTH_BASE_URL + "oauth2/token", auth_request=True, data={
            "grant_type": "authorization_code", "redirect_uri": OAUTH_CALLBACK_URI, "client_id": OAUTH_CLIENT_ID,
            "code": values["code"][0], "code_verifier": verifier, "scope": OAUTH_LOGIN_SCOPE})
        if not isinstance(token.get("id_token"), str) or not token["id_token"]:
            raise AuthenticationError("Nissan did not return an identity token.")
        # The vehicle API requires separate access/refresh tokens from the Nissan backend.
        self._install_token(self._json("POST", BFF_BASE_URL + "v1/oauth2/access_token?platform=Android",
                                       auth_request=True, headers={"Authorization": token["id_token"],
                                                                   "Content-Type": JSON_API_CONTENT_TYPE}))

    def _install_token(self, token):
        if not isinstance(token.get("access_token"), str) or not token["access_token"]:
            raise AuthenticationError("Nissan did not return an access token.")
        try:
            lifetime_seconds = float(token.get("expires_in", DEFAULT_TOKEN_LIFETIME_SECONDS))
            if not math.isfinite(lifetime_seconds) or lifetime_seconds <= 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            raise AuthenticationError("Nissan returned an invalid token lifetime.") from None
        self._access_token = token["access_token"]
        self._refresh_token = token.get("refresh_token") or self._refresh_token
        self._expires_at_monotonic_seconds = time.monotonic() + max(0, lifetime_seconds - TOKEN_REFRESH_MARGIN_SECONDS)

    def _authenticate(self, force=False):
        if self._access_token and not force and time.monotonic() < self._expires_at_monotonic_seconds:
            return
        if self._refresh_token:
            try:
                self._install_token(self._json("POST", BFF_BASE_URL + "v1/oauth2/refresh-token?platform=Android",
                                               auth_request=True, headers={"Authorization": self._refresh_token,
                                                                           "Content-Type": JSON_API_CONTENT_TYPE},
                                               json={"scope": "openid profile vehicles"}))
                return
            except AuthenticationError:
                pass  # A rejected refresh token requires a new login.
        self._login()

    def _get(self, url):
        # Retry authorization once; scheduling and service-error retries belong to Core.
        for force in (False, True):
            self._authenticate(force=force)
            try:
                return self._json("GET", url, headers={"Authorization": "Bearer " + self._access_token,
                                                       "Content-Type": JSON_API_CONTENT_TYPE})
            except AuthenticationError:
                if force:
                    self._access_token = self._refresh_token = None
                    raise

    def _select_vehicle(self):
        user_id = self._get(USERS_BASE_URL + "v1/users/current").get("userId")
        if not isinstance(user_id, str) or not user_id:
            raise NissanError("Nissan did not return a user identifier.")
        vehicles = self._get(BFF_BASE_URL + "v5/users/" + quote(user_id, safe="") + "/cars").get("data")
        if not isinstance(vehicles, list):
            raise NissanError("Nissan did not return a vehicle list.")
        candidates = {v["vin"].upper() for v in vehicles if isinstance(v, dict) and isinstance(v.get("vin"), str)
                      and re.fullmatch(VIN_PATTERN, v["vin"].upper())}
        if self._configured_vin:
            if self._configured_vin not in candidates:
                raise NissanError("The configured VIN was not found in the Nissan account.")
            self._vin = self._configured_vin
        elif len(candidates) == 1:
            self._vin = candidates.pop()
        else:
            raise NissanError("Could not select a unique vehicle. Please configure the VIN.")

    def fetch_battery(self) -> Tuple[float, Optional[float], float, Optional[float]]:
        """Return SoC (%), range (km), battery measurement time (Unix seconds), odometer (km).

        Range and odometer may be None; valid zero values are preserved. The timestamp
        belongs only to the battery data, not the separately retrieved odometer.
        Battery or required login failures raise NissanError. Odometer failures do not
        invalidate a valid SoC and return None for mileage.
        """
        if not self._vin:
            self._select_vehicle()
        url = CARS_BASE_URL + "v1/cars/" + self._vin
        soc_percent, range_km, measurement_unix_seconds = parse_battery(self._get(url + "/battery-status"))
        # Cockpit availability differs by vehicle. Never discard a valid SoC or invent mileage.
        odometer_km = None
        try:
            odometer_km = _number(self._get(url + "/cockpit")["data"]["attributes"]["totalMileage"])
        except (NissanError, KeyError, TypeError):
            log.debug("Nissan odometer unavailable.")
        log.debug("Nissan battery measurement_unix_seconds=%s", measurement_unix_seconds)
        return soc_percent, range_km, measurement_unix_seconds, odometer_km
