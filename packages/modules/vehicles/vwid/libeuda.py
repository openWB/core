#!/usr/bin/env python3
"""Client for the VW EU Data Act portal (OIDC login + data delivery)."""

from __future__ import annotations

from typing import Union
from asyncio import new_event_loop, set_event_loop
import uuid
import logging
import aiohttp
import io
import json
import re
import zipfile
from html.parser import HTMLParser
from urllib.parse import urlencode, urljoin, urlparse
from datetime import datetime, timezone, timedelta
import time
import threading
import asyncio
# from helpermodules.pub import Pub
import glob
import os
import os.path
from pathlib import Path
from collections import deque
from helpermodules.constants import RAMDISK_PATH
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.vwid.config import VWId

"""Constants for the VW EU Data Act integration."""

# --- Portal / OIDC endpoints ---------------------------------------------
BASE_URL = "https://eu-data-act.drivesomethinggreater.com"
IDENTITY_BASE = "https://identity.vwgroup.io"

# Brand is part of the OIDC state; VW passenger cars by default.
# BRAND = "VOLKSWAGEN_PASSENGER_CARS"
CALLBACK_LOGIN_PATH = "/services/callbacklogin"

BRANDS: dict[str, dict[str, str]] = {
    "volkswagen": {
        "display_name": "Volkswagen",
        "client_id": "9b58543e-1c15-4193-91d5-8a14145bebb0@apps_vw-dilab_com",
        "state": "VOLKSWAGEN_PASSENGER_CARS",
    },
    "audi": {
        "display_name": "Audi",
        "client_id": "cc29b87a-5e9a-4362-aecf-5adea6b01bbb@apps_vw-dilab_com",
        "state": "AUDI",
    },
    "skoda": {
        "display_name": "Škoda",
        "client_id": "3ea88bf9-1d4e-4a68-b3ad-4098c1f1d246@apps_vw-dilab_com",
        "state": "SKODA",
    },
    "seat": {
        "display_name": "SEAT",
        "client_id": "f85e5b69-e3b2-43aa-9c0d-1b7d0e0b576f@apps_vw-dilab_com",
        "state": "SEAT",
    },
    "cupra": {
        "display_name": "CUPRA",
        "client_id": "f85e5b69-e3b2-43aa-9c0d-1b7d0e0b576f@apps_vw-dilab_com",
        "state": "CUPRA",
    },
}


DEFAULT_BRAND = "volkswagen"
DEFAULT_COUNTRY = "de"
DEFAULT_LANGUAGE = "en"


def ano_part(original):
    return original[0] + ('*' * (len(original) - 2)) + original[-1]


def ano_email(original):
    user, at, domain = original.partition('@')
    domain_name, dot, tld = domain.rpartition('.')
    return '{}@{}.{}'.format(ano_part(user), ano_part(domain_name), tld)


def ano_vin(vin: str) -> str:
    return vin[:-9] + "*********"


def get_oidc_client_id(brand: str = DEFAULT_BRAND) -> str:
    """Return the OIDC client_id for the given brand."""
    return BRANDS.get(brand, BRANDS[DEFAULT_BRAND])["client_id"]


def get_oidc_state(brand: str = DEFAULT_BRAND) -> str:
    """Return the OIDC state for the given brand."""
    brand_state = BRANDS.get(brand, BRANDS[DEFAULT_BRAND])["state"]
    return f"{DEFAULT_COUNTRY}__{DEFAULT_LANGUAGE}__{brand_state}"


# OIDC: we build the authorize URL directly instead of using the portal's
# /services/redirect/authentication servlet, which returns HTTP 500 for
# non-browser clients (it depends on AEM browser session state).
OIDC_AUTHORIZE_URL = IDENTITY_BASE + "/oidc/v1/authorize"
# OIDC_CLIENT_ID = "9b58543e-1c15-4193-91d5-8a14145bebb0@apps_vw-dilab_com"
OIDC_SCOPE = "openid cars profile"
OIDC_REDIRECT_URI = BASE_URL + "/login"
# state encodes country__language__brand (echoed back to the portal callback).
# DEFAULT_COUNTRY = "si"
# DEFAULT_LANGUAGE = "sl"
CONF_BRAND = "brand"
# OIDC_STATE = f"{DEFAULT_COUNTRY}__{DEFAULT_LANGUAGE}__{BRAND}"

# Legacy constants for backward compatibility (default to VW)
OIDC_CLIENT_ID = BRANDS[DEFAULT_BRAND]["client_id"]
OIDC_STATE = get_oidc_state(DEFAULT_BRAND)

# proxy_api paths (relative to BASE_URL)
VEHICLES_PATH = "/proxy_api/consent/me/vehicles"
RELATION_PATH = "/proxy_api/vum/v2/users/me/relations/{vin}"
METADATA_PATH = "/proxy_api/euda-apim/datarequest/vehicles/{vin}/metadata/partial"
LIST_PATH = "/proxy_api/euda-apim/datadelivery/vehicles/{vin}/{identifier}/list"
DOWNLOAD_PATH = "/proxy_api/euda-apim/datadelivery/vehicles/{vin}/{identifier}/download"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

# --- Config entry keys ----------------------------------------------------
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_VIN = "vin"
CONF_IDENTIFIER = "identifier"
CONF_NICKNAME = "nickname"

# --- Scheduling -----------------------------------------------------------
# Datasets land ~every 15 min; refresh shortly after the next expected drop.
DATASET_INTERVAL = timedelta(minutes=15)
POST_DATASET_BUFFER = timedelta(seconds=45)
RETRY_INTERVAL = timedelta(minutes=1)
MIN_INTERVAL = timedelta(seconds=30)

# Files with this suffix carry no payload and are skipped.
NO_CONTENT_SUFFIX = "_no_content_found.zip"

POLL_INTERVAL = 60    # polling interval in seconds
CYCLE_INTERVAL = 600  # cycle interval in seconds
INITIAL_RESULT_WAIT = 30  # seconds to wait for the first background result
EUDA_THREADNAME = "soc_bt_ev"
UTC = None
KEEP_JSON = 5
DATA_PATH = Path(__file__).resolve().parents[4] / "data" / "modules" / "vwid"
JSON_PATH = Path(str(RAMDISK_PATH) + '/vweuda')
storeFileName = '/data_'
MODULE_TYPE = 'vwid'

# VIN-Brand map
VIN_BRAND_MAP = {
    "WAU": "audi",           # Audi car
    "WA1": "audi",           # Audi SUV
    "WUA": "audi",           # Audi Sport car
    "WU1": "audi",           # Audi Sport SUV
    "99A": "audi",           # Audi 2016-
    "AAA": "audi",           # Audi South-Africa-
    "TRU": "audi",           # Audi Hungary
    "VSS": "cupra",          # Seat/Cupra - assume cupra as default
    "NAD": "skoda",          # Skoda
    "TMB": "skoda",          # Skoda (Czech Republic)
    "Y6U": "skoda",          # Skoda Auto made by Eurocar (Ukraine)
    "VWV": "volkswagen",     # Volkswagen Spain
    "WVG": "volkswagen",     # SUV/Touran
    "WVW": "volkswagen",     # Passenger Cars
    "WV1": "volkswagen",     # Commercial Vehicles
    "WV2": "volkswagen",     # Commercial Vehicles
    "WV3": "volkswagen",     # Commercial Vehicles
    "WV4": "volkswagen",     # Commercial Vehicles
    "WV5": "volkswagen",     # Commercial Vehicles
}


_LOGGER = logging.getLogger(__name__)


class ApiError(Exception):
    """Generic API failure."""


class AuthError(ApiError):
    """Authentication failed or session expired."""


class _FormParser(HTMLParser):
    """Extract the first <form> action and all hidden/input fields."""

    def __init__(self) -> None:
        super().__init__()
        self.action: str | None = None
        self.fields: dict[str, str] = {}
        self._in_form = False
        self._done = False  # only capture the first form

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._done:
            return
        a = dict(attrs)
        if tag == "form" and self.action is None:
            self.action = a.get("action")
            self._in_form = True
        elif tag == "input" and self._in_form:
            name = a.get("name")
            if name:
                self.fields[name] = a.get("value") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._in_form:
            self._in_form = False
            self._done = True


def _parse_form(html: str) -> _FormParser:
    p = _FormParser()
    p.feed(html)
    return p


def _extract_template_model(html: str) -> dict:
    """Extract the VW identity ``templateModel`` JSON embedded in the page.

    The signin/authenticate pages carry their form state (hmac, relayState,
    prefilled email, postAction, error) in a JS object rather than HTML inputs:

        window._IDK = { templateModel: { ... }, csrf_token: '...' }
    """
    idx = html.find("templateModel")
    if idx == -1:
        return {}
    brace = html.find("{", idx)
    if brace == -1:
        return {}
    depth = 0
    for i in range(brace, len(html)):
        c = html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[brace: i + 1])
                except ValueError:
                    return {}
    return {}


def _extract_csrf(html: str) -> str | None:
    """Pull the csrf_token out of the identity page's JS."""
    m = re.search(r"csrf_token\s*[:=]\s*['\"]([^'\"]+)['\"]", html)
    return m.group(1) if m else None


def _login_fields(html: str) -> tuple[dict[str, str], str | None]:
    """Collect the fields needed to POST a VW identity login step.

    Merges HTML hidden inputs with the JS templateModel/csrf so it works
    whether the page renders inputs server-side (email step) or via JS
    (password step). Returns (fields, form_action)."""
    form = _parse_form(html)
    fields: dict[str, str] = dict(form.fields)
    model = _extract_template_model(html)
    if model:
        for key in ("hmac", "relayState"):
            if model.get(key):
                fields[key] = model[key]
        email = (model.get("emailPasswordForm") or {}).get("email")
        if email:
            fields.setdefault("email", email)
    csrf = _extract_csrf(html)
    if csrf:
        fields.setdefault("_csrf", csrf)
    return fields, form.action


def _login_error(html: str) -> str | None:
    """Return a human-readable login error from the page, if present."""
    model = _extract_template_model(html)
    err = model.get("error") or model.get("errorCode")
    if isinstance(err, dict):
        return err.get("text") or err.get("errorCode") or str(err)
    return str(err) if err else None


def _extract_vins(payload) -> list[dict]:
    """Best-effort extraction of vehicles from the (undocumented) vehicles body.

    Returns a list of {vin, nickname?} dicts. Walks the JSON for any 17-char
    VIN-like identifier so it is robust to wrapper shape ({vehicles:[]}, list, …).
    """
    vins: dict[str, dict] = {}

    def walk(node):
        if isinstance(node, dict):
            vin = node.get("vin") or node.get("vehicleIdentificationNumber")
            if isinstance(vin, str) and len(vin) == 17:
                vins.setdefault(vin, {"vin": vin})
                nick = node.get("vehicleNickname") or node.get("nickname") or node.get("modelName")
                if nick:
                    vins[vin]["nickname"] = nick
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(payload)
    return list(vins.values())


class EudaApiClient:
    """Authenticated client for the EU Data Act portal."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str, brand: str = "volkswagen") -> None:
        self._session = session
        self._email = email
        self._password = password
        self._brand = brand
        self._logged_in = False

    # -- low level ---------------------------------------------------------

    async def _get(self, url: str, *, headers: dict | None = None, allow_redirects: bool = True):
        h = {"User-Agent": USER_AGENT, **(headers or {})}
        return await self._session.get(url, headers=h, allow_redirects=allow_redirects)

    # -- authentication ----------------------------------------------------

    async def async_login(self) -> None:
        """Run the full OIDC login, populating the session cookie jar."""
        try:
            await self._do_login()
        except aiohttp.ClientError as err:
            raise ApiError(f"Network error during login: {err}") from err
        self._logged_in = True

    async def _do_login(self) -> None:
        # 0. Prime the portal session (the browser loads the site first; this
        #    sets the AEM load-balancer/session cookies the callback needs).
        try:
            async with await self._get(f"{BASE_URL}/") as resp:
                await resp.read()
        except aiohttp.ClientError as err:
            _LOGGER.debug("login step0: priming GET failed (ignored): %s", err)

        # 1. Start the OIDC flow directly at the identity provider. We build the
        #    authorize URL ourselves because the portal's
        #    /services/redirect/authentication servlet returns HTTP 500 for
        #    non-browser clients.
        authorize_url = self._build_authorize_url(self._brand)
        _LOGGER.debug("login step1: authorize url = %s", authorize_url)
        async with await self._get(authorize_url) as resp:
            signin_url = str(resp.url)
            signin_html = await resp.text()
        _LOGGER.debug("login step2: signin page = %s (%d bytes)", signin_url, len(signin_html))

        # 2. POST the email (identifier step). Fields come from HTML inputs
        #    and/or the JS templateModel (hmac, _csrf, relayState).
        fields, action = _login_fields(signin_html)
        _LOGGER.debug("login step2: action=%s fields=%s", action, sorted(fields))
        if "hmac" not in fields or "_csrf" not in fields:
            raise AuthError(
                f"Could not parse the sign-in form (fields found: {sorted(fields)})"
            )
        fields["email"] = self._email
        identifier_action = urljoin(signin_url, action or "")
        async with self._session.post(
            identifier_action,
            data=fields,
            headers={"User-Agent": USER_AGENT, "Referer": signin_url},
        ) as resp:
            authenticate_url = str(resp.url)
            authenticate_html = await resp.text()
            status = resp.status
        _LOGGER.debug(
            "login step3: after identifier POST status=%s url=%s", status, authenticate_url
        )

        # 3. The identifier step lands on the password (authenticate) page,
        #    whose hidden fields live in the JS templateModel, not HTML inputs.
        fields2, action2 = _login_fields(authenticate_html)
        _LOGGER.debug("login step3: action=%s fields=%s", action2, sorted(fields2))
        if "hmac" not in fields2 or "_csrf" not in fields2:
            err = _login_error(authenticate_html)
            raise AuthError(
                err
                or "Identity portal did not return the password form - check the "
                "email address (or the login flow changed)"
            )
        fields2["email"] = self._email
        fields2["password"] = self._password
        # The browser posts to the clean /login/authenticate URL with relayState
        # in the body; posting to authenticate_url (which carries ?relayState=)
        # duplicates it and is rejected with HTTP 400. Strip the query.
        if action2:
            authenticate_action = urljoin(authenticate_url, action2)
        else:
            authenticate_action = authenticate_url.split("?", 1)[0]
        _LOGGER.debug("login step4: POST credentials to %s", authenticate_action)

        # 4. POST credentials; follow the redirect chain back to the portal,
        #    which sets the session cookies via /services/callbacklogin.
        async with self._session.post(
            authenticate_action,
            data=fields2,
            headers={"User-Agent": USER_AGENT, "Referer": authenticate_url},
        ) as resp:
            landing = str(resp.url)
            landing_html = await resp.text()
            if resp.status >= 400:
                _LOGGER.debug(
                    "login step4: HTTP %s body[:500]=%s", resp.status, landing_html[:500]
                )
                err = _login_error(landing_html)
                raise AuthError(err or f"Login rejected (HTTP {resp.status})")
        _LOGGER.debug("login step4: landed on %s", landing)

        # Positively confirm success: a completed flow lands back on the portal
        # host (via /services/callbacklogin). Bad credentials re-render the
        # identity sign-in page (URL still on identity.vwgroup.io/signin-service).
        portal_host = urlparse(BASE_URL).netloc
        if "signin-service" in landing or "/error" in landing:
            raise AuthError("Login failed - check email and password")
        if urlparse(landing).netloc != portal_host:
            raise AuthError(f"Login did not complete (ended at {landing})")

    @staticmethod
    def _build_authorize_url(brand: str = "volkswagen") -> str:
        """Construct the OIDC authorize URL (bypasses the broken AEM servlet)."""
        params = {
            "client_id": get_oidc_client_id(brand),
            "response_type": "code",
            "scope": OIDC_SCOPE,
            "state": get_oidc_state(brand),
            "redirect_uri": OIDC_REDIRECT_URI,
            "prompt": "login",
        }
        return f"{OIDC_AUTHORIZE_URL}?{urlencode(params)}"

    # -- authenticated requests -------------------------------------------

    async def _get_json(self, url: str, *, headers: dict | None = None, _retry: bool = True):
        async with await self._get(url, headers=headers) as resp:
            if resp.status in (401, 403) and _retry:
                _LOGGER.debug("Session expired (%s) for %s; re-authenticating", resp.status, url)
                self._logged_in = False
                await self.async_login()
                return await self._get_json(url, headers=headers, _retry=False)
            if resp.status >= 400:
                raise ApiError(f"GET {url} -> HTTP {resp.status}")
            text = await resp.text()
        try:
            return json.loads(text)
        except ValueError as err:
            raise ApiError(f"Invalid JSON from {url}: {err}") from err

    async def async_ensure_login(self) -> None:
        if not self._logged_in:
            await self.async_login()

    async def async_list_vehicles(self) -> list[dict]:
        await self.async_ensure_login()
        payload = await self._get_json(f"{BASE_URL}{VEHICLES_PATH}?viewPosition=FRONT_LEFT")
        vehicles = _extract_vins(payload)
        # Always enrich with the friendly vehicleNickname from the relation
        # endpoint (the authoritative source, e.g. "ID.3").
        for veh in vehicles:
            try:
                rel = await self.async_get_relation(veh["vin"])
                nickname = (rel.get("relation") or {}).get("vehicleNickname")
                _LOGGER.debug("relation for %s: nickname=%r", veh["vin"], nickname)
                if nickname:
                    veh["nickname"] = nickname
            except ApiError as err:
                _LOGGER.debug("Could not fetch nickname for %s: %s", veh["vin"], err)
        return vehicles

    async def async_get_relation(self, vin: str) -> dict:
        await self.async_ensure_login()
        # The relation endpoint requires a traceid header; it returns HTTP 400
        # without one.
        headers = {"traceid": f"vehicle-relation-fetch-{uuid.uuid4()}"}
        return await self._get_json(
            f"{BASE_URL}{RELATION_PATH.format(vin=vin)}", headers=headers
        )

    async def async_get_metadata(self, vin: str) -> dict:
        """Return the data-request metadata; ``Identifier`` is needed downstream."""
        await self.async_ensure_login()
        return await self._get_json(f"{BASE_URL}{METADATA_PATH.format(vin=vin)}")

    async def async_list_datasets(self, vin: str, identifier: str) -> list[dict]:
        """Return the rolling list of available zips: [{name, createdOn, size}]."""
        await self.async_ensure_login()
        url = f"{BASE_URL}{LIST_PATH.format(vin=vin, identifier=identifier)}"
        # The list endpoint requires the data-request type header (matching
        # metadata/partial); without it the backend returns HTTP 500.
        data = await self._get_json(url, headers={"type": "partial"})
        return data if isinstance(data, list) else data.get("files", [])

    async def async_download_dataset(self, vin: str, identifier: str, name: str) -> Union[str, dict]:
        """Download a specific zip by name and return the parsed JSON inside it."""
        await self.async_ensure_login()
        if name.endswith(NO_CONTENT_SUFFIX):
            raise ApiError(f"{name} contains no content")
        url = f"{BASE_URL}{DOWNLOAD_PATH.format(vin=vin, identifier=identifier)}"
        headers = {"filename": name, "type": "partial"}
        async with await self._get(url, headers=headers) as resp:
            if resp.status in (401, 403):
                self._logged_in = False
                await self.async_login()
                async with await self._get(url, headers=headers) as resp2:
                    if resp2.status >= 400:
                        raise ApiError(f"Download {name} -> HTTP {resp2.status}")
                    raw = await resp2.read()
            elif resp.status >= 400:
                raise ApiError(f"Download {name} -> HTTP {resp.status}")
            else:
                raw = await resp.read()
        _data = self._unzip_json(raw, name)
        _name = name.replace('.zip', '.json')
        return _name, _data

    @staticmethod
    def _unzip_json(raw: bytes, name: str) -> dict:
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                members = [n for n in zf.namelist() if n.lower().endswith(".json")]
                if not members:
                    raise ApiError(f"No JSON inside {name}")
                with zf.open(members[0]) as fh:
                    return json.loads(fh.read().decode("utf-8"))
        except (zipfile.BadZipFile, ValueError) as err:
            raise ApiError(f"Could not read {name}: {err}") from err


async def _async_try_login(session, client) -> str | None:
    """Attempt login + vehicle discovery; return an error key or None."""
    try:
        await client.async_login()
        _vehicles = await client.async_list_vehicles()
        _LOGGER.info(f"_vehicles={_vehicles}")
    except AuthError:
        return "invalid_auth"
    except ApiError:
        return "cannot_connect"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error during login")
        return "unknown"
    return None


async def _async_update_data(client, vin, identifier) -> Union[str, str]:
    await client.async_ensure_login()
    # await client.async_login()
    try:
        listing = await client.async_list_datasets(vin, identifier)
    except AuthError as err:
        # Retry soon rather than waiting the full ~15-min cadence.
        # self.update_interval = RETRY_INTERVAL
        raise ApiError(f"Authentication failed: {err}") from err
    except ApiError as err:
        # self.update_interval = RETRY_INTERVAL
        if "HTTP 400" in str(err):
            _LOGGER.info(f"err={err}")
            # The data-delivery endpoint returns 400 until the portal has
            # finished provisioning a newly enabled continuous data request,
            # which can take a few hours. HA keeps retrying until it's ready.
            raise ApiError(
                "Data delivery not ready yet (HTTP 400). If you just enabled "
                "the continuous data request on the portal, it can take a few "
                "hours to start; will keep retrying."
            ) from err
        raise ApiError(str(err)) from err

    # content datasets, oldest -> newest by createdOn
    content = sorted(
        (e for e in listing if e.get("name") and not e["name"].endswith(NO_CONTENT_SUFFIX)),
        key=lambda e: _created_on(e) or datetime.min.replace(tzinfo=timezone.utc),
    )
    _LOGGER.debug("refresh: %d listed, %d with content", len(listing), len(content))

    if not content:
        raise ApiError("No datasets with content available yet")

    # Load the newest dataset for live state. (We don't backfill history into
    # statistics: importing into recorder-managed sensor entities collides
    # with the recorder's own statistics and can corrupt unrelated ones.)
    newest = content[-1]

    try:
        name, payload = await client.async_download_dataset(
            vin, identifier, newest["name"]
        )
    except ApiError as err:
        raise ApiError(f"Could not download newest dataset: {err}") from err

    return name, payload


def _filename_timestamp(name: str) -> datetime | None:
    """Parse a YYYYMMDDhhmmss segment from a dataset filename.

    Handles both layouts seen in the wild ("TIMESTAMP_VIN.zip" and
    "VIN_TIMESTAMP.zip") by scanning the underscore-separated parts
    right-to-left for the first one that parses as a timestamp.
    """
    stem = name.rsplit(".", 1)[0]
    for part in reversed(stem.split("_")):
        try:
            return datetime.strptime(part, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _created_on(entry: dict) -> datetime | None:
    raw = entry.get("createdOn")
    if not raw:
        return _filename_timestamp(entry.get("name", ""))
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return _filename_timestamp(entry.get("name", ""))


def get_field_value_by_key(D: dict, key: str, field: str) -> str:
    ret = None
    for f in D:
        if f['key'] == key:
            ret = f['value']
    if ret:
        _LOGGER.info(f"get_field_value_by_key: field: {field}, {key} -> {ret}")
    return ret


def get_field_timestamp_by_key(D: dict, key: str) -> str:
    ret = None
    for f in D:
        if f['key'] == key:
            ret = f['timestampUtc']
    if ret:
        _LOGGER.info(f"get_field_timestamp_by_key {key} -> {ret}")
    return ret


CAR_TIMESTAMP = "car_captured_time"


def get_max_value_by_fieldname(D: dict, field: str) -> str:
    ret = "-"
    key = None
    for f in D:
        if f['dataFieldName'] == field:
            v = f['value']
            if ret == "-":
                ret = v
                key = f['key']
            else:
                if v > ret:
                    ret = v
                    key = f['key']
    if ret == "-":
        _LOGGER.info(f"get_max_value_by_fieldname {field}: no match")
        ret = None
    else:
        _LOGGER.info(f"get_max_value_by_fieldname {field} -> {ret}, key={key}")
    return ret


def utc_to_timestamp(d: str) -> float:
    _epoch = datetime(1970, 1, 1)
    _utcformat = "%Y-%m-%dT%H:%M:%SZ"
    _d = re.sub(r'\....Z', 'Z', d)
    _dt = datetime.strptime(_d, _utcformat)
    _ts = (_dt - _epoch).total_seconds()
    return _ts


def parse_vehicle_data(payload: dict) -> dict:
    """Extract normalized SoC fields from an EUDA JSON payload."""
    data = payload.get('Data', [])
    soc = get_field_value_by_key(data, 'ae0294b4-1286-3e98-a818-1485b8d88430', 'soc')
    soc_timestamp_str = None
    if soc is not None:
        _LOGGER.info(f"soc {soc} found in state_of_charge")
        _ts = get_field_timestamp_by_key(data, 'ae0294b4-1286-3e98-a818-1485b8d88430')
        soc_timestamp_str = re.sub(r'\....Z', 'Z', _ts)
    if soc_timestamp_str is None:
        soc_timestamp_str = get_max_value_by_fieldname(data, CAR_TIMESTAMP)

    if soc is None:
        soc = get_field_value_by_key(data, 'f89ed652-d104-3fa6-b7e2-ab7543309e7b', 'soc')
    if soc is None:
        soc = get_field_value_by_key(data, '506cb83e-f99f-3af3-bbeb-0429b69a78d9', 'soc')
    if soc is None:
        soc = get_field_value_by_key(data, 'ac1108b1-b8cc-3db9-a663-03d387e42223', 'soc')
    range = get_field_value_by_key(data, '153e8c40-4c6c-3c17-a11b-0ecc35d55b81', 'range')
    if range is None:
        range = get_field_value_by_key(data, '0ca40e18-0564-3eda-bcc0-7aee9ef44f04', 'range')
    odometer = get_field_value_by_key(data, '41c0805c-43e5-313e-9dfb-356cb8d20f7c', 'odometer')
    if odometer is None:
        odometer = get_field_value_by_key(data, '30cc36fd-71ca-3c09-9296-e94ebd47bd2b', 'odometer')
    if soc_timestamp_str:
        soc_timestamp = utc_to_timestamp(soc_timestamp_str)
        if soc_timestamp > 1e10:
            soc_timestamp = soc_timestamp / 1000
    else:
        _LOGGER.warning("soc_timestamp not found!")

    return {
        'soc': soc,
        'range': range,
        'soc_timestamp': soc_timestamp,
        'soc_timestamp_str': soc_timestamp_str,
        'odometer': odometer,
    }


class euda():

    # _LOGGER.setLevel(logging.DEBUG)
    client = {}
    thread = {}
    result = {}
    files = {}
    tests_done = False

    def __init__(self):
        # make sure required folders are there
        try:
            _LOGGER.debug("DATA_PATH=" + str(DATA_PATH))
            DATA_PATH.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            _LOGGER.exception("init: dataPath creation failed, dataPath: " +
                              str(DATA_PATH) + ", error=" + str(e))

        try:
            _LOGGER.debug("JSON_PATH=" + str(JSON_PATH))
            JSON_PATH.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            _LOGGER.exception("init: JSON_PATH creation failed, dataPath: " +
                              str(JSON_PATH) + ", error=" + str(e))

    def save_json_file(self, _name: str, vin: str, _data: dict) -> bool:
        status = False
        if vin not in euda.files:
            euda.files[vin] = deque(maxlen=KEEP_JSON)
        if _name not in euda.files[vin]:
            euda.files[vin].append(_name)
            status = True

        fname = str(JSON_PATH) + '/' + _name
        if not os.path.isfile(fname):
            with open(fname, 'w') as f:
                _LOGGER.debug(f"save json file {fname.replace(vin, ano_vin(vin))}")
                json.dump(_data, f, indent=4)
            # status = True
        else:
            _LOGGER.debug(f"file {fname.replace(vin, ano_vin(vin))} not saved because is exists already")

        # cleanup old file except the latest KEEP_JSON!
        _l = glob.glob(str(JSON_PATH) + '/*_' + vin + '.json')
        _l.sort()
        _len = len(_l)
        _del = _len - KEEP_JSON

        _la = []
        for _x in _l:
            _la.append(_x.replace(vin, ano_vin(vin)))

        _LOGGER.debug(f"cleanup: KEEP_JSON={KEEP_JSON}, _l={_la}\n _len ={_len}, _del={_del}")
        if _del > 0:
            _del_list = _l[0:_del]
            _da = []
            for _x in _del_list:
                _da.append(_x.replace(vin, ano_vin(vin)))
            _LOGGER.debug(f"cleanup: _del_list={_da}")
            for f in _del_list:
                os.remove(f)
                _LOGGER.debug(f"delete json file {f.replace(vin, ano_vin(vin))}")

        return status

    def update_result_from_payload(self, payload: dict, source: str) -> dict:
        """Parse an EUDA payload and publish it in the in-memory result cache."""
        vin = payload['vin']
        result = parse_vehicle_data(payload)
        _valid = True
        _LOGGER.info(f"latest result=\n{json.dumps(result, indent=4)}")
        if vin in euda.result:
            _LOGGER.info(f"cache result=\n{json.dumps(euda.result[vin], indent=4)}")
            if result['soc_timestamp'] < euda.result[vin]['soc_timestamp']:
                _LOGGER.info("thread result skipped, soc_timestamp too old")
                _valid = False
            if result['soc'] is None:
                _LOGGER.info("thread result skipped, no soc found")
                _valid = False
        if _valid:
            if vin in euda.result and result['odometer'] < euda.result[vin]['odometer']:
                _LOGGER.info("odometer less than earlier - keep earlier value")
                result['odometer'] = euda.result[vin]['odometer']
            euda.result[vin] = result
            _LOGGER.info("thread result is valid")

        _ano_j = {ano_vin(vin): euda.result[vin]}
        _LOGGER.info(f"\n{json.dumps(_ano_j, indent=4)}")

        return result

    def load_latest_json_result(self, vin: str) -> bool:
        """Load and parse the newest already downloaded EUDA JSON for a VIN."""
        files = glob.glob(str(JSON_PATH) + '/*_' + vin + '.json')
        files.sort()
        if not files:
            return False
        latest = files[-1]
        try:
            with open(latest) as f:
                payload = json.load(f)
            self.update_result_from_payload(payload, latest)
            return True
        except Exception as err:
            _LOGGER.exception(f"failed to load latest EUDA JSON {latest}: {err}")
            return False

    async def get_module_type(self, vehicle: int) -> str:
        topic = f"openWB/vehicle/{vehicle}/soc_module/config"
        conf = os.popen(f"mosquitto_sub -C 1 -t {topic}").read()
        _LOGGER.debug(f"thread loop: conf={conf}")
        _type = json.loads(conf)['type']
        return _type

    # eudaThread
    async def async_eudaThread(self, username: str, password: str, vin: str, vehicle: int):
        if vin[0:3] not in VIN_BRAND_MAP:
            _LOGGER.warning(f"VIN {vin[0:3]} not in brand map, use {DEFAULT_BRAND}")
        brand = VIN_BRAND_MAP.get(vin[0:3], DEFAULT_BRAND)
        _LOGGER.info(f"async Thread started, brand={brand}")
        try:
            async with aiohttp.ClientSession(headers={'Connection': 'keep-alive'},
                                             connector_owner=False) as session:
                client_id = f"{vehicle}"
                _k = str(euda.client.keys())
                _LOGGER.info(f"libeuda.Thread client at entry: euda.client.keys={_k}")
                if client_id not in euda.client:
                    _LOGGER.debug(f"create new client, key={client_id}")
                    euda.client[client_id] = {}
                    euda.client[client_id] = EudaApiClient(session, username, password, brand)
                    _k = str(euda.client.keys())
                    _LOGGER.info(f"libeuda.Thread client: euda.client.keys={_k}")

                meta = None
                while meta is None:
                    try:
                        meta = await euda.client[client_id].async_get_metadata(vin)
                    except ApiError as err:
                        if "HTTP 500" in str(err):
                            _LOGGER.info(f"Portal not ready/get_metadata, wait {POLL_INTERVAL} seconds")
                        else:
                            _LOGGER.exception(f"APIError/get_metadata: {err}")
                        meta = None
                    except Exception as err:
                        _LOGGER.exception(f"Exception/get_metadata: {err}")
                        meta = None
                    if meta is None:
                        time.sleep(POLL_INTERVAL)

                identifier = meta.get("Identifier")

                # thread main loop
                _active = True
                while _active:
                    _type = await self.get_module_type(vehicle)
                    _LOGGER.info(f"thread loop: ev{vehicle} module type={_type}")
                    if _type != MODULE_TYPE:
                        _LOGGER.info(f"vehicle {vehicle} is not using module vwid: terminate now")
                        _active = False
                        continue
                    try:
                        _data = None
                        while _data is None:
                            try:
                                _name, _data = await _async_update_data(euda.client[client_id], vin, identifier)
                            except ApiError as err:
                                if "HTTP 500" in str(err):
                                    _LOGGER.info(f"Portal not ready/update_data, wait {POLL_INTERVAL} seconds")
                                    _data = None
                                else:
                                    _LOGGER.exception(f"thread APIError {err}")
                                    _data = None
                            except Exception as err:
                                _LOGGER.exception(f"thread Exception {err}")
                                _data = None
                            if _data is None:
                                await asyncio.sleep(POLL_INTERVAL)

                        vin = _data['vin']
                        self.save_json_file(_name, vin, _data)
                        self.update_result_from_payload(_data, _name)
                        _LOGGER.info(f"sleep {CYCLE_INTERVAL} seconds")
                        await asyncio.sleep(CYCLE_INTERVAL)

                    except Exception as e:
                        _LOGGER.exception(f"thread loop failed 0, exception={e}")

        except Exception as e:
            _LOGGER.exception(f"thread body failed 0, exception={e}")

    def eudaThread(self, username: str, password: str, vin: str, vehicle: int):
        _LOGGER.info(f"sync libeuda.eudaThread {threading.current_thread().name} started")
        asyncio.run(self.async_eudaThread(username, password, vin, vehicle))
        _LOGGER.info(f"sync libeuda.eudaThread {threading.current_thread().name} ended")

    def check_tests(self):
        _l = glob.glob(str(DATA_PATH) + '/test_*' + '.json')
        for _t in _l:
            _vin = _t[_t.index('_')+1:].replace('.json', '')
            _LOGGER.info(f"found test file: {_t}, vin={_vin}")
            with open(_t) as f:
                payload = json.load(f)
                result = parse_vehicle_data(payload)

                test_result = {}
                test_result[_vin] = result
                _ano_j = json.dumps(test_result, indent=4).replace(_vin, ano_vin(_vin))
                _LOGGER.info(f"test_result, vin={_vin}:\n{_ano_j}")

    async def get_status(self,
                         conf: VWId,
                         vehicle: int,
                         vehicle_update_data: VehicleUpdateData) -> Union[int, float, str, float, float]:

        # error codes SOCERR-xx raised:
        # SOCERR-00: general error
        # SOCERR-01: login problem, username, password wrong, account locked, etc.
        # SOCERR-02: vehicle not (yet) found in portal, VIN wrong?

        if not euda.tests_done:
            self.check_tests()
            euda.tests_done = True

        self.username = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.vehicle = vehicle
        _LOGGER.debug(f"update_data:{vehicle_update_data}")
        self.average_consump = vehicle_update_data.average_consump
        self.battery_capacity = vehicle_update_data.battery_capacity

        try:
            self.storeFile = str(DATA_PATH) + storeFileName + str(self.vin) + '.json'
            if os.path.isfile(self.storeFile):
                _LOGGER.debug(f"load data from {self.storeFile.replace(self.vin, ano_vin(self.vin))}")
                with open(self.storeFile) as f:
                    data = json.load(f)
            else:
                data = {}
                data['currentSOC_pct'] = str(0)
                data['cruisingRangeElectric_km'] = str(0)
                data['carCapturedTimestamp'] = "1970-01-01T00:00:00Z"
                data['soc_timestamp'] = str(0)
                data['odometer'] = str(0)

            thread_id = f"{self.vehicle}"
            euda.thread[thread_id] = {}
            euda.thread[thread_id]['name'] = f"{EUDA_THREADNAME}{self.vehicle}"
            euda.thread[thread_id]['thread'] = None
            for t in threading.enumerate():
                if t.name == euda.thread[thread_id]['name']:
                    _LOGGER.debug(f"thread {t.name} exists already")
                    euda.thread[thread_id]['thread'] = t
            if euda.thread[thread_id]['thread'] is None:
                _LOGGER.debug(f"{euda.thread[thread_id]['name']} not found: starting now")
                euda.thread[thread_id]['thread'] = threading.Thread(target=self.eudaThread,
                                                                    name=euda.thread[thread_id]['name'],
                                                                    args=(self.username,
                                                                          self.password,
                                                                          self.vin,
                                                                          self.vehicle),
                                                                    daemon=True)
                euda.thread[thread_id]['thread'].start()

            if self.vin not in euda.result:
                self.load_latest_json_result(self.vin)

            wait_until = time.time() + INITIAL_RESULT_WAIT
            while self.vin not in euda.result and time.time() < wait_until:
                _LOGGER.info(f"wait for first EUDA result for VIN {ano_vin(self.vin)}")
                time.sleep(1)

            if self.vin in euda.result:
                _LOGGER.debug(f"vehicle match: {ano_vin(self.vin)}")
                _ano_j = {}
                for vin in euda.result:
                    _ano_j[ano_vin(vin)] = euda.result[vin]
                _LOGGER.info(f"result from thread:\n{json.dumps(_ano_j, indent=4)}")
                soc = euda.result[self.vin]['soc']
                range = euda.result[self.vin]['range']
                try:
                    soc_pct = float(soc) if soc is not None else 0.0
                except (TypeError, ValueError):
                    soc_pct = 0.0
                if soc_pct > 0 and range is None:
                    range = int(soc_pct * float(self.battery_capacity) / float(self.average_consump))
                    _LOGGER.warning(f"no range delivered, calculate range = {range}km")

                ts = euda.result[self.vin]['soc_timestamp']
                ts_str = euda.result[self.vin]['soc_timestamp_str']
                odometer = euda.result[self.vin]['odometer']

                _LOGGER.debug(f"vin             = {self.vin}")
                _LOGGER.debug(f"soc             = {soc}")
                _LOGGER.debug(f"range           = {range}")
                _LOGGER.debug(f"soc_timestamp   = {ts}")
                _LOGGER.debug(f"soc_timestamp_str = {ts_str}")
                _LOGGER.debug(f"odometer        = {odometer}")

                data_modified = False
                if soc and str(soc) != data['currentSOC_pct']:
                    data['currentSOC_pct'] = str(soc)
                    data_modified = True
                if range and str(range) != data['cruisingRangeElectric_km']:
                    data['cruisingRangeElectric_km'] = str(range)
                    data_modified = True
                if ts and str(ts) != data['soc_timestamp']:
                    data['soc_timestamp'] = str(ts)
                    data_modified = True
                if ts_str and str(ts_str) != data['carCapturedTimestamp']:
                    data['carCapturedTimestamp'] = str(ts_str)
                    data_modified = True
                if odometer and str(odometer) != data['odometer']:
                    data['odometer'] = str(odometer)
                    data_modified = True

                # save data to file if modified
                if data_modified or not os.path.isfile(self.storeFile):
                    _LOGGER.info(f"save data to {self.storeFile}")
                    with open(self.storeFile, 'w') as f:
                        json.dump(data, f, indent=4)

            else:
                _LOGGER.error(f"SOCERR-02: Für VIN {ano_vin(self.vin)} wurden (noch) keine Daten gefunden")
                # raise Exception(f"SOCERR-02: Für VIN {self.vin} wurden (noch) keine Daten gefunden")

            _LOGGER.info(f"return data:\n{json.dumps(data, indent=4)}")
            soc = data['currentSOC_pct']
            range = data['cruisingRangeElectric_km']
            ts = data['soc_timestamp']
            ts_str = data['carCapturedTimestamp']
            odometer = data['odometer']
            _LOGGER.info(f"get_status: soc={soc}, range={range}, ts={ts}, ts_str={ts_str}, odometer={odometer}")

            # for test only:
            # set soc_timestamp to 0 to avoid computed state being later than this reported state
            # topic = f"openWB/vehicle/{self.vehicle}/get/soc_timestamp"
            # ep0 = 0
            # _LOGGER.info(f"get_status: publish soc_timestamp as 0: topic: {topic}, message: {ep0}")
            # Pub().pub(topic, ep0)

            return float(soc), float(range), float(ts), ts_str, float(odometer)
        except Exception as e:
            _LOGGER.exception(f"get_status failed 0, exception={e}")
            # if exception is a SOCERR reraise it, otherwise raise general SOCERR-00
            if "SOCERR" in str(e):
                raise e
            else:
                _t = f"SOCERR-00: Für User {ano_email(self.username)}"
                _t = _t + f" und VIN {ano_vin(self.vin)} wurden keine Daten empfangen"
                raise Exception(f"{_t} {e}")


# sync function
def fetch_soc(conf: VWId,
              vehicle: int,
              vehicle_update_data: VehicleUpdateData) -> Union[float, float, float, str, float]:

    # prepare and call async method
    loop = new_event_loop()
    set_event_loop(loop)

    # get soc, range from server
    a = euda()
    soc, range, soc_ts, soc_tsX, odometer =\
        loop.run_until_complete(a.get_status(conf, vehicle, vehicle_update_data))

    return soc, range, soc_ts, soc_tsX, odometer
