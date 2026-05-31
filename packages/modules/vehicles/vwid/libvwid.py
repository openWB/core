#!/usr/bin/env python3
"""Communicate with Volkswagen Connect services."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import hashlib
from json import dumps as to_json
from json import loads
import uuid
import logging
from random import randint, random
from urllib.parse import parse_qs, urljoin, urlparse

from aiohttp import ClientSession, ClientTimeout, client_exceptions
from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT
from bs4 import BeautifulSoup
import jwt

ANDROID_PACKAGE_NAME = "com.volkswagen.weconnect"
APP_URI = "weconnect://authenticated"
BASE_API = "https://emea.bff.cariad.digital"
BASE_AUTH = "https://identity.vwgroup.io"
BASE_SESSION = "https://msg.volkswagen.de"
BRAND = "VW"
USER_AGENT = "Volkswagen/3.61.0-android/14"
CLIENT_ID = "a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com"
COUNTRY = "DE"
HEADERS_SESSION = {
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Accept-charset": "UTF-8",
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
    "x-platform": "android",
    "x-assertion": "0",
    "x-android-package-name": ANDROID_PACKAGE_NAME,
}
HEADERS_AUTH = {
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
              "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": USER_AGENT,
    "x-platform": "android",
    "x-assertion": "0",
    "x-android-package-name": ANDROID_PACKAGE_NAME,
}

MAX_RETRIES_ON_RATE_LIMIT = 3
TIMEOUT = timedelta(seconds=30)
JWT_ALGORITHMS = ["RS256"]
CLIENT_TOKEN_TYPES = "code"
CLIENT_SCOPE = "openid profile badge cars dealers vin offline_access"


"""Custom exceptions for volkswagencarnet."""


class VWError(Exception):
    """Base exception for VW CarNet errors."""

    pass


class AuthenticationError(VWError):
    """Authentication failed."""

    pass


class APIError(VWError):
    """API request failed."""

    pass


class SPINError(VWError):
    """S-PIN related error."""

    pass


class RedirectError(VWError):
    """Redirect handling failed."""

    pass


class RequestError(VWError):
    """Request execution failed."""

    pass


class TermsAndConditionsError(AuthenticationError):
    """Terms and Conditions need to be accepted."""

    pass


class Services:
    """Service names that are used in `capabilities` and `selectivestatus` calls."""

    CHARGING = "charging"
    PARAMETERS = "parameters"
    SERVICE_STATUS = "service_status"
    MEASUREMENTS = "measurements"


def find_path_in_dict(src, path) -> object:
    """Return data at path in dictionary source.

    Simple navigation of a hierarchical dict structure using XPATH-like syntax.

    >>> find_path_in_dict(dict(a=1), 'a')
    1

    >>> find_path_in_dict(dict(a=1), '')
    {'a': 1}

    >>> find_path_in_dict(dict(a=None), 'a')


    >>> find_path_in_dict(dict(a=1), 'b')
    Traceback (most recent call last):
    ...
    KeyError: 'b'

    >>> find_path_in_dict(dict(a=dict(b=1)), 'a.b')
    1

    >>> find_path_in_dict(dict(a=dict(b=1)), 'a')
    {'b': 1}

    >>> find_path_in_dict(dict(a=dict(b=1)), 'a.c')
    Traceback (most recent call last):
    ...
    KeyError: 'c'

    """
    if not path:
        return src
    if isinstance(path, str):
        path = path.split(".")
    if isinstance(src, list):
        try:
            f = float(path[0])
            if f.is_integer() and len(src) > 0:
                return find_path_in_dict(src[int(f)], path[1:])
            raise KeyError("Key not found")
        except ValueError as valerr:
            raise KeyError(f"{path[0]} should be an integer") from valerr
        except IndexError as idxerr:
            raise KeyError("Index out of range") from idxerr
    return find_path_in_dict(src[path[0]], path[1:])


def find_path(src, path) -> object:
    """Return data at path in source."""
    try:
        return find_path_in_dict(src, path)
    except KeyError:
        _LOGGER.error(
            "Dictionary path: %s is no longer present. Dictionary: %s", path, src
        )
        return None


def is_valid_path(src, path):
    """Check if path exists in source.

    >>> is_valid_path(dict(a=1), 'a')
    True

    >>> is_valid_path(dict(a=1), '')
    True

    >>> is_valid_path(dict(a=1), None)
    True

    >>> is_valid_path(dict(a=1), 'b')
    False

    >>> is_valid_path({"a": [{"b": True}, {"c": True}]}, 'a.0.b')
    True

    >>> is_valid_path({"a": [{"b": True}, {"c": True}]}, 'a.1.b')
    False
    """
    try:
        find_path_in_dict(src, path)
    except KeyError:
        return False
    else:
        return True


UTC = None
BACKEND_RECEIVED_TIMESTAMP = "BACKEND_RECEIVED_TIMESTAMP"

_LOGGER = logging.getLogger(__name__)


class Vehicle:
    """Vehicle contains the state of sensors and methods for interacting with the car."""

    def __init__(self, conn, url) -> None:
        """Initialize the Vehicle with default values."""
        self._connection = conn
        self._url = url
        self._homeregion = "https://msg.volkswagen.de"
        self._discovered = False
        self._states = {}
        self._requests: dict[str, object] = {
            "departuretimer": {"status": "", "timestamp": datetime.now(UTC)},
            "batterycharge": {"status": "", "timestamp": datetime.now(UTC)},
            "climatisation": {"status": "", "timestamp": datetime.now(UTC)},
            "refresh": {"status": "", "timestamp": datetime.now(UTC)},
            "lock": {"status": "", "timestamp": datetime.now(UTC)},
            "latest": "",
            "state": "",
        }

        # API Endpoints that might be enabled for car (that we support)
        self._services: dict[str, dict[str, object]] = {
            Services.CHARGING: {"active": False},
            Services.PARAMETERS: {},
        }

    def _in_progress(self, topic: str, unknown_offset: int = 0) -> bool:
        """Check if request is already in progress."""
        if self._requests.get(topic, {}).get("id", False):
            timestamp = self._requests.get(topic, {}).get(
                "timestamp",
                datetime.now(UTC) - timedelta(minutes=unknown_offset),
            )
            if timestamp + timedelta(minutes=3) < datetime.now(UTC):
                self._requests.get(topic, {}).pop("id")
            else:
                _LOGGER.debug("Action (%s) already in progress", topic)
                return True
        return False

    async def _handle_response(
        self, response, topic: str, error_msg: str | None = None
    ) -> bool:
        """Handle errors in response and get requests remaining."""
        if not response:
            self._requests[topic] = {
                "status": "Failed",
                "timestamp": datetime.now(UTC),
            }
            _LOGGER.error(
                error_msg
                if error_msg is not None
                else f"Failed to perform {topic} action"
            )
            raise Exception(
                error_msg
                if error_msg is not None
                else f"Failed to perform {topic} action"
            )
        self._requests[topic] = {
            "timestamp": datetime.now(UTC),
            "status": response.get("state", "Unknown"),
            "id": response.get("id", 0),
        }
        if response.get("state", None) == "Throttled":
            status = "Throttled"
            _LOGGER.warning("Request throttled (%s)", topic)
        else:
            status = await self.wait_for_request(request=response.get("id", 0))
        self._requests[topic] = {
            "status": status,
            "timestamp": datetime.now(UTC),
        }
        return True

    # API get and set functions #
    # Init and update vehicle data
    async def discover(self):
        """Discover vehicle and initial data."""

        _LOGGER.debug("Attempting discovery of supported API endpoints for vehicle")

        capabilities_response = await self._connection.getOperationList(self.vin)
        parameters_list = capabilities_response.get("parameters", {})
        capabilities_list = capabilities_response.get("capabilities", {})

        # Update services with parameters
        if parameters_list:
            self._services[Services.PARAMETERS].update(parameters_list)

        # If there are no capabilities, log a warning
        if not capabilities_list:
            _LOGGER.warning(
                "Could not determine available API endpoints for %s", self.vin
            )
            self._discovered = True
            return

        for service_id, service in capabilities_list.items():
            if service_id not in self._services:
                continue

            service_name = service.get("id", "Unknown Service")
            data = {}

            if service.get("isEnabled", False):
                data["active"] = True
                _LOGGER.debug("Discovered enabled service: %s", service_name)

                expiration_date = service.get("expirationDate", None)
                if expiration_date:
                    data["expiration"] = expiration_date

                operations = service.get("operations", {})
                data["operations"] = [op.get("id", None) for op in operations.values()]

                parameters = service.get("parameters", [])
                data["parameters"] = parameters

            else:
                reason = service.get("status", "Unknown reason")
                _LOGGER.debug(
                    "Service: %s is disabled due to: %s", service_name, reason
                )
                data["active"] = False

            # Update the service data
            try:
                self._services[service_name].update(data)
            except Exception as error:
                _LOGGER.warning(
                    'Exception "%s" while updating service "%s": %s',
                    error,
                    service_name,
                    data,
                )

        _LOGGER.debug("API endpoints: %s", self._services)
        self._discovered = True

    async def update(self):
        """Try to fetch data for all known API endpoints."""
        _LOGGER.debug("connection update")
        if not self._discovered:
            _LOGGER.debug("connection discover")
            await self.discover()
        if not self.deactivated:
            _LOGGER.debug("connection gather selective status charging")
            await asyncio.gather(
                self.get_selectivestatus(
                    [
                        Services.CHARGING,
                        Services.MEASUREMENTS,
                    ]
                )
            )
            await asyncio.gather(self.get_service_status())
        else:
            _LOGGER.warning("Vehicle with VIN %s is deactivated", self.vin)

    # Data collection functions
    async def get_selectivestatus(self, services):
        """Fetch selective status for specified services."""
        data = await self._connection.getSelectiveStatus(self.vin, services)
        if data:
            self._states.update(data)

    async def get_vehicle(self):
        """Fetch car masterdata."""
        _LOGGER.debug("get_vehicle for Vehicle with VIN %s", self.vin)
        data = await self._connection.getVehicleData(self.vin)
        if data:
            self._states.update(data)

    async def get_service_status(self):
        """Fetch service status."""
        data = await self._connection.get_service_status()
        if data:
            self._states.update({Services.SERVICE_STATUS: data})

    # Refresh vehicle data (VSR)
    async def set_refresh(self):
        """Wake up vehicle and update status data."""
        if self._in_progress("refresh", unknown_offset=-5):
            return False
        try:
            self._requests["latest"] = "Refresh"
            response = await self._connection.wakeUpVehicle(self.vin)
            if response:
                if response.status == 204:
                    self._requests["state"] = "in_progress"
                    self._requests["refresh"] = {
                        "timestamp": datetime.now(UTC),
                        "status": "in_progress",
                        "id": 0,
                    }
                    status = await self.wait_for_data_refresh()
                elif response.status == 429:
                    status = "Throttled"
                    _LOGGER.debug("Server side throttled. Try again later")
                else:
                    _LOGGER.debug(
                        "Unable to refresh the data. Incorrect response code: %s",
                        response.status,
                    )
                self._requests["state"] = status
                self._requests["refresh"] = {
                    "status": status,
                    "timestamp": datetime.now(UTC),
                }
                return True
            _LOGGER.debug("Unable to refresh the data")
        except Exception as error:
            _LOGGER.warning("Failed to execute data refresh - %s", error)
            self._requests["refresh"] = {
                "status": "Exception",
                "timestamp": datetime.now(UTC),
            }
        raise Exception("Data refresh failed")

    # Vehicle class helpers #
    # Vehicle info
    @property
    def attrs(self):
        """Return all attributes.

        :return:
        """
        return self._states

    def has_attr(self, attr) -> bool:
        """Return true if attribute exists.

        :param attr:
        :return:
        """
        return is_valid_path(self.attrs, attr)

    def get_attr(self, attr):
        """Return a specific attribute.

        :param attr:
        :return:
        """
        return find_path(self.attrs, attr)

    async def expired(self, service):
        """Check if access to service has expired."""
        try:
            now = datetime.now(UTC)
            if self._services.get(service, {}).get("expiration", False):
                expiration = self._services.get(service, {}).get("expiration", False)
                if not expiration:
                    expiration = datetime.neow(UTC) + timedelta(days=1)
            else:
                _LOGGER.debug(
                    "Could not determine end of access for service %s, assuming it is valid",
                    service,
                )
                expiration = datetime.now(UTC) + timedelta(days=1)
            expiration = expiration.replace(tzinfo=None)
            if now >= expiration:
                _LOGGER.info("Access to %s has expired!", service)
                self._discovered = False
                return True
        except Exception:
            _LOGGER.debug(
                "Exception. Could not determine end of access for service %s, assuming it is valid",
                service,
            )
            return False
        else:
            return False

    @property
    def vin(self) -> str:
        """Vehicle identification number.

        :return:
        """
        return self._url

    @property
    def deactivated(self) -> bool | None:
        """Return true if service is deactivated.

        :return:
        """
        return self.attrs.get("carData", {}).get("deactivated", None)

    # Helper functions #
    def __str__(self):
        """Return the vin."""
        return self.vin


def json_loads(s) -> object:
    """Load JSON from string and parse timestamps."""
    return loads(s, object_hook=obj_parser)


def obj_parser(obj: dict) -> dict:
    """Parse datetime."""
    for key, val in obj.items():
        try:
            obj[key] = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
        except (TypeError, ValueError):
            """The value was not a date."""
    return obj


# noinspection PyPep8Naming
class Connection:
    """Connection to VW-Group Connect services."""

    _login_lock = asyncio.Lock()

    # Init connection class
    def __init__(
        self,
        session,
        username,
        password,
        country=COUNTRY,
        interval=timedelta(minutes=5),
    ) -> None:
        """Initialize."""
        self._session = session
        self._session_headers = HEADERS_SESSION.copy()
        self._session_auth_headers = HEADERS_AUTH.copy()
        self._session_refresh_interval = interval
        self._session_logged_in = False
        self._session_first_update = False
        self._session_auth_username = username
        self._session_auth_password = password
        self._session_tokens = {}
        self._session_country = country.upper()

        self._vehicles = []

        self._jarCookie = None

        self._service_status = {}

    def _clear_cookies(self):
        self._session._cookie_jar._cookies.clear()  # pylint: disable=protected-access

    # API Login
    async def doLogin(self, tries: int = 1):
        """Login method, clean login."""
        async with self._login_lock:
            _LOGGER.debug("Initiating new login")

            for i in range(tries):
                self._session_logged_in = await self._login()
                if self._session_logged_in:
                    break
                if i > tries:
                    _LOGGER.error("Login failed after %s tries", tries)
                    return False
                await asyncio.sleep(random() * 5)

            if not self._session_logged_in:
                return False

            _LOGGER.info("Successfully logged in")

            # Get list of vehicles from account
            _LOGGER.debug("Fetching vehicles associated with account")
            self._session_headers.pop("Content-Type", None)
            loaded_vehicles = await self.get(url=f"{BASE_API}/vehicle/v2/vehicles")
            # Add Vehicle class object for all VIN-numbers from account
            if loaded_vehicles.get("data") is not None:
                _LOGGER.debug("Found vehicle(s) associated with account")
                self._vehicles = []
                for vehicle in loaded_vehicles.get("data"):
                    self._vehicles.append(Vehicle(self, vehicle.get("vin")))
            else:
                _LOGGER.warning("Failed to login to Volkswagen Connect API")
                self._session_logged_in = False
                return False

            # Update all vehicles data before returning
            await self.update()
            return True

    async def get_openid_config(self) -> dict[str, str]:
        """Get OpenID config."""
        _LOGGER.debug("Requesting openid config")
        req = await self._session.get(
            url=f"{BASE_API}/auth/v1/idk/oidc/openid-configuration"
        )
        if req.status != 200:
            _LOGGER.error("Failed to get OpenID configuration, status: %s", req.status)
            raise AuthenticationError(
                f"OpenID configuration error: status {req.status}"
            )
        config = await req.json()
        _LOGGER.debug("OpenID config: %s", config)
        return config

    async def get_authorization_page(self, authorization_endpoint: str) -> str:
        """Fetch the Auth0 Universal Login page for credential submission.

        Hits the OIDC authorization endpoint with response_type=code id_token token
        (hybrid flow). Auth0 redirects to the login form; we follow that single
        redirect and return the HTML so the caller can extract the state token.
        """
        _LOGGER.debug('Requesting authorization page from "%s"', authorization_endpoint)
        self._session_auth_headers.pop("Referer", None)
        self._session_auth_headers.pop("Origin", None)

        params = {
            "redirect_uri": APP_URI,
            # Hybrid flow: Auth0 returns code + id_token + access_token in the
            # callback so no separate token exchange with the CARIAD BFF is needed.
            "response_type": "code id_token token",
            "client_id": CLIENT_ID,
            "scope": CLIENT_SCOPE,
            "nonce": uuid.uuid4().hex,
        }

        req = await self._session.get(
            url=authorization_endpoint,
            headers=self._session_auth_headers,
            allow_redirects=False,
            params=params,
        )

        location = req.headers.get("Location")
        if not location:
            raise AuthenticationError(
                f"Missing 'Location' header in authorization response. "
                f"Status: {req.status}"
            )

        ref = urljoin(authorization_endpoint, location)
        if "error" in ref:
            parsed_query = parse_qs(urlparse(ref).query)
            error_msg = parsed_query.get("error", ["Unknown error"])[0]
            error_description = parsed_query.get(
                "error_description", ["No description"]
            )[0]
            _LOGGER.info("Authorization error: %s", error_description)
            raise AuthenticationError(f"{error_msg}: {error_description}")

        # Follow the redirect to the actual login page
        req = await self._session.get(
            url=ref, headers=self._session_auth_headers, allow_redirects=False
        )
        if req.status != 200:
            raise AuthenticationError(f"Failed to fetch login page (HTTP {req.status})")

        return await req.text()

    def extract_state_token(self, page_content: str) -> str | None:
        """Extract state token from a page."""
        soup = BeautifulSoup(page_content, "html.parser")
        state_input = soup.select_one('input[name="state"]')
        if not state_input or not state_input.get("value"):
            _LOGGER.debug("State token not found.")
            return None
        return state_input["value"]

    async def post_form(
        self, session, url: str, headers: dict, form_data: dict, redirect: bool = True
    ) -> str:
        """Post a form and check for success."""
        req = await session.post(
            url, headers=headers, data=form_data, allow_redirects=redirect
        )

        # Redirect case
        if not redirect and req.status == 302:
            return req.headers.get("Location")

        # Handle explicit error 400 (form validation failure)
        if req.status == 400:
            page_content = await req.text()
            soup = BeautifulSoup(page_content, "html.parser")

            # Try both username + password fields in one pass
            for field_id in ("error-element-username", "error-element-password"):
                span = soup.select_one(f'span[id="{field_id}"]')
                if not span:
                    continue

                error_code = span.get("data-error-code")
                if error_code == "wrong-email-credentials":
                    raise AuthenticationError("Wrong username or password")

            # Unknown 400 error
            raise AuthenticationError(
                "Login form validation failed with unknown 400 error"
            )

        # Any unexpected HTTP code
        if req.status not in (200, 400):
            raise RequestError(
                f"Login form submission failed with HTTP {req.status}. "
                "This might indicate incorrect credentials or a temporary service issue."
            )

        # Normal success path
        return await req.text()

    async def follow_redirects(
        self, session, pw_url: str, redirect_location: str
    ) -> str:
        """Handle redirects."""
        ref = urljoin(pw_url, redirect_location)
        max_depth = 10
        while not ref.startswith(APP_URI):
            if max_depth == 0:
                raise RedirectError(
                    f"Too many redirects during login flow (max depth: {max_depth}). "
                    "This might indicate an authentication loop."
                )
            response = await session.get(
                url=ref, headers=self._session_auth_headers, allow_redirects=False
            )

            # Check if we hit a terms and conditions page (HTTP 200 with no redirect)
            if response.status == 200 and "Location" not in response.headers:
                page_content = await response.text()
                if (
                    "termsAndConditions" in page_content
                    or '"page":"termsAndConditions"' in page_content
                ):
                    _LOGGER.error(
                        "Terms and Conditions acceptance required. "
                        "Please log in to https://www.myvolkswagen.net/ and accept the updated terms."
                    )
                    raise TermsAndConditionsError(
                        "Terms and Conditions must be accepted. "
                        "Please visit https://www.myvolkswagen.net/ to accept the updated terms and conditions, "
                        "then try logging in again."
                    )

            if "Location" not in response.headers:
                _LOGGER.warning("Failed to find next redirect location")
                raise RedirectError("Failed to find next redirect location")
            ref = urljoin(ref, response.headers["Location"])
            max_depth -= 1
        return ref

    async def _get_authorization_code(self, openid_config: dict) -> tuple:
        """Run the OIDC hybrid login flow and return the callback tokens.

        Uses response_type=code id_token token so identity.vwgroup.io (Auth0)
        delivers access_token and id_token directly in the callback — these are
        usable with the CARIAD BFF without a separate token exchange step.

        Returns:
            Tuple of (auth_code_jwt, id_token, access_token)
        """
        authorization_endpoint = openid_config["authorization_endpoint"]
        auth_issuer = openid_config["issuer"]

        authorization_page = await self.get_authorization_page(authorization_endpoint)

        state_token = self.extract_state_token(authorization_page)
        if not state_token:
            _LOGGER.error(
                "Unable to find valid login page. "
                "Try logging in to the portal: https://www.myvolkswagen.net/"
            )
            raise AuthenticationError("Invalid login page - missing state token")

        login_form = {
            "username": self._session_auth_username,
            "password": self._session_auth_password,
            "state": state_token,
            "action": "default",
        }
        login_url = f"{auth_issuer}/u/login?state={state_token}"

        redirect_location = await self.post_form(
            self._session,
            login_url,
            self._session_auth_headers,
            login_form,
            False,
        )

        callback_url = await self.follow_redirects(
            self._session, auth_issuer, redirect_location
        )

        parsed = urlparse(callback_url)
        all_params = {**parse_qs(parsed.query), **parse_qs(parsed.fragment)}
        _LOGGER.debug("Callback params keys: %s", list(all_params.keys()))

        auth_code = all_params.get("code", [None])[0]
        id_token = all_params.get("id_token", [None])[0]
        access_token = all_params.get("access_token", [None])[0]

        if not auth_code:
            raise AuthenticationError("No authorization code in callback URL")

        return auth_code, id_token, access_token

    def _build_session_tokens(
        self, auth_code: str, id_token: str, access_token: str
    ) -> dict:
        """Build the session token dict from the hybrid OIDC callback values.

        The hybrid flow (response_type=code id_token token) already delivers
        access_token and id_token directly from identity.vwgroup.io. These
        Auth0-issued tokens are valid for the CARIAD BFF, which validates them
        against Auth0's public keys. No separate token exchange is required.

        Note: the authorization code (auth_code) is not used for a server-side
        exchange — it is decoded here only for debug logging.
        """
        try:
            payload = jwt.decode(auth_code, options={"verify_signature": False})
            _LOGGER.debug("Auth code JWT payload: %s", payload)
        except Exception:
            _LOGGER.debug("Auth code is not a JWT, continuing without decode")

        return {
            "access_token": access_token,
            "id_token": id_token,
            "token_type": "Bearer",
        }

    async def _login(self) -> bool:
        """Login function.

        Returns:
            True if login successful, False otherwise
        """
        try:
            # Clear cookies and reset headers
            self._clear_cookies()
            self._session_headers = HEADERS_SESSION.copy()
            self._session_auth_headers = HEADERS_AUTH.copy()

            # Get OpenID configuration (authorization_endpoint, issuer)
            openid_config = await self.get_openid_config()

            # Get authorization code and hybrid tokens from login flow
            auth_code, id_token, access_token = await self._get_authorization_code(
                openid_config
            )

            # Build session tokens from hybrid flow response (no server-side exchange needed)
            tokens = self._build_session_tokens(auth_code, id_token, access_token)

            # Validate token structure
            required_keys = ["access_token", "id_token", "token_type"]
            if not all(key in tokens for key in required_keys):
                _LOGGER.error(
                    "Invalid token response. Missing required keys. Got: %s",
                    list(tokens.keys()),
                )
                self._session_logged_in = False
                return False

            # Store directly as "identity"
            self._session_tokens["identity"] = tokens

            # Update authorization header
            self._session_headers["Authorization"] = (
                "Bearer " + self._session_tokens["identity"]["access_token"]
            )

            _LOGGER.debug("Successfully stored authentication tokens")

            # Mark session as logged in
            self._session_logged_in = True
            return True

        except (AuthenticationError, RequestError, RedirectError) as error:
            _LOGGER.error("Authentication error during login: %s", error)
            self._session_logged_in = False
            return False
        except client_exceptions.ClientError as error:
            _LOGGER.error("Network error during login: %s", error)
            self._session_logged_in = False
            return False
        except KeyError as error:
            _LOGGER.error("Missing required data during login: %s", error)
            self._session_logged_in = False
            return False
        except Exception as error:
            _LOGGER.error("Unexpected error during login: %s", error)
            self._session_logged_in = False
            return False

    async def _handle_action_result(self, response_raw):
        response = await response_raw.json(loads=json_loads)
        if not response:
            raise APIError("Invalid or no response from action endpoint")
        if response == 429:
            return {"id": None, "state": "Throttled"}
        request_id = response.get("data", {}).get("requestID", 0)
        _LOGGER.debug("Request returned with request id: %s", request_id)
        return {"id": str(request_id)}

    async def terminate(self):
        """Log out from connect services."""
        _LOGGER.info("Initiating logout")
        await self.logout()

    async def logout(self):
        """Logout, revoke tokens."""
        self._session_headers.pop("Authorization", None)

        if self._session_logged_in:
            if self._session_tokens.get("identity", {}).get("refresh_token"):
                _LOGGER.info("Revoking Identity Refresh Token")
                params = {"token": self._session_tokens["identity"]["refresh_token"]}
                await self.post(f"{BASE_API}/auth/v1/idk/oidc/revoke", data=params)

    # HTTP methods to API
    async def _request(self, method, url, return_raw=False, **kwargs):
        """Perform a query to the VW-Group API."""
        _LOGGER.debug('HTTP %s "%s"', method, url)
        if kwargs.get("json", None):
            _LOGGER.debug("Request payload: %s", kwargs.get("json", None))
        try:
            async with self._session.request(
                method,
                url,
                headers=self._session_headers,
                timeout=ClientTimeout(total=TIMEOUT.seconds),
                cookies=self._jarCookie,
                raise_for_status=False,
                **kwargs,
            ) as response:
                response.raise_for_status()

                # Update cookie jar
                if self._jarCookie is not None:
                    self._jarCookie.update(response.cookies)
                else:
                    self._jarCookie = response.cookies

                # Update service status
                await self.update_service_status(url, response.status)

                try:
                    if response.status == 204:
                        if return_raw:
                            res = response
                        else:
                            res = {"status_code": response.status}
                    elif 200 <= response.status < 300:
                        res = await response.json(loads=json_loads)
                    else:
                        res = {}
                        _LOGGER.debug(
                            "Not success status code [%s] response: %s",
                            response.status,
                            response.text,
                        )
                except Exception:  # pylint: disable=broad-exception-caught
                    res = {}
                    _LOGGER.debug(
                        "Something went wrong [%s] response: %s",
                        response.status,
                        response.text,
                    )
                    if return_raw:
                        return response
                    return res

                _LOGGER.debug(
                    'Request for "%s" returned with status code [%s], headers: %s, response: %s',
                    url,
                    response.status,
                    response.headers,
                    res,
                )

                if return_raw:
                    res = response
                return res
        except client_exceptions.ClientResponseError as httperror:
            # Update service status
            await self.update_service_status(url, httperror.status)
            raise httperror from None
        except Exception as error:
            # Update service status
            await self.update_service_status(url, 1000)
            raise error from None

    async def get(self, url, vin="", tries=0):
        """Perform a get query."""
        try:
            return await self._request(METH_GET, url)
        except client_exceptions.ClientResponseError as error:
            if error.status == 400:
                _LOGGER.error(
                    'Got HTTP 400 "Bad Request" from server, this request might be malformed or not implemented'
                    " correctly for this vehicle"
                )
            elif error.status == 401:
                _LOGGER.warning(
                    'Received "unauthorized" error while fetching data: %s', error
                )
                self._session_logged_in = False
            elif error.status == 429 and tries < MAX_RETRIES_ON_RATE_LIMIT:
                delay = randint(1, 3 + tries * 2)
                _LOGGER.debug(
                    "Server side throttled. Waiting %s, try %s", delay, tries + 1
                )
                await asyncio.sleep(delay)
                return await self.get(url, vin, tries + 1)
            elif error.status == 500:
                _LOGGER.debug(
                    "Got HTTP 500 from server, service might be temporarily unavailable"
                )
            elif error.status == 502:
                _LOGGER.debug(
                    "Got HTTP 502 from server, this request might not be supported for this vehicle"
                )
            else:
                _LOGGER.error("Got unhandled error from server: %s", error.status)
            return {"status_code": error.status}

    async def post(self, url, vin="", tries=0, return_raw=False, **data):
        """Perform a post query."""
        try:
            if data:
                return await self._request(
                    METH_POST, url, return_raw=return_raw, **data
                )
            return await self._request(METH_POST, url, return_raw=return_raw)
        except client_exceptions.ClientResponseError as error:
            if error.status == 429 and tries < MAX_RETRIES_ON_RATE_LIMIT:
                delay = randint(1, 3 + tries * 2)
                _LOGGER.debug(
                    "Server side throttled. Waiting %s, try %s", delay, tries + 1
                )
                await asyncio.sleep(delay)
                return await self.post(
                    url, vin, tries + 1, return_raw=return_raw, **data
                )
            raise

    async def put(self, url, vin="", tries=0, return_raw=False, **data):
        """Perform a put query."""
        try:
            if data:
                return await self._request(METH_PUT, url, return_raw=return_raw, **data)
            return await self._request(METH_PUT, url, return_raw=return_raw)
        except client_exceptions.ClientResponseError as error:
            if error.status == 429 and tries < MAX_RETRIES_ON_RATE_LIMIT:
                delay = randint(1, 3 + tries * 2)
                _LOGGER.debug(
                    "Server side throttled. Waiting %s, try %s", delay, tries + 1
                )
                await asyncio.sleep(delay)
                return await self.put(
                    url, vin, tries + 1, return_raw=return_raw, **data
                )
            raise

    # Update data for all Vehicles
    async def update(self):
        """Update status."""
        if not self.logged_in:
            if not await self._login():
                _LOGGER.warning("Login for %s account failed!", BRAND)
                return False
        try:
            if not await self.validate_tokens():
                _LOGGER.info(
                    "Session expired. Initiating new login for %s account", BRAND
                )
                if not await self.doLogin():
                    _LOGGER.warning("Login for %s account failed!", BRAND)
                    raise AuthenticationError(f"Login for {BRAND} account failed")
            else:
                _LOGGER.debug("Going to call vehicle updates")
                # Get all Vehicle objects and update in parallell
                updatelist = [vehicle.update() for vehicle in self.vehicles]
                # Wait for all data updates to complete
                await asyncio.gather(*updatelist)

                return True
        except (OSError, LookupError, Exception) as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not update information: %s", error)
        return False

    async def getPendingRequests(self, vin):
        """Get status information for pending requests."""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/pendingrequests"
            )

            if response:
                response["refreshTimestamp"] = datetime.now(UTC)
                return response

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning(
                "Could not fetch information for pending requests, error: %s", error
            )
        return False

    async def getOperationList(self, vin):
        """Collect operationlist for VIN, supported/licensed functions."""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/capabilities", ""
            )
            if response.get("capabilities", False):
                data = response
            elif response.get("status_code", {}):
                _LOGGER.warning(
                    "Could not fetch operation list, HTTP status code: %s",
                    response.get("status_code"),
                )
                data = response
            else:
                _LOGGER.info("Could not fetch operation list: %s", response)
                data = {"error": "unknown"}
        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch operation list, error: %s", error)
            data = {"error": "unknown"}
        return data

    async def getSelectiveStatus(self, vin, services):
        """Get status information for specified services."""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/selectivestatus?jobs={','.join(services)}",
                "",
            )

            for service in services:
                if not response.get(service):
                    _LOGGER.debug(
                        "Did not receive return data for requested service %s.\
                         (This is expected for several service/car combinations)",
                        service,
                    )

            if response:
                response.update({"refreshTimestamp": datetime.now(UTC)})
                return response

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch selectivestatus, error: %s", error)
        return False

    async def getVehicleData(self, vin):
        """Get car information like VIN, nickname, etc."""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(f"{BASE_API}/vehicle/v2/vehicles", "")

            for vehicle in response.get("data"):
                if vehicle.get("vin") == vin:
                    return {"vehicle": vehicle}

            _LOGGER.warning("Could not fetch vehicle data for vin %s", vin)

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch vehicle data, error: %s", error)
        return False

    async def getParkingPosition(self, vin):
        """Get information about the parking position."""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/parkingposition", ""
            )

            if "data" in response:
                return {"isMoving": False, "parkingposition": response["data"]}
            if response.get("status_code", {}):
                if response.get("status_code", 0) == 204:
                    _LOGGER.debug(
                        "Seems car is moving, HTTP 204 received from parkingposition"
                    )
                    return {"isMoving": True, "parkingposition": {}}

                _LOGGER.warning(
                    "Could not fetch parkingposition, HTTP status code: %s",
                    response.get("status_code"),
                )
            else:
                _LOGGER.info(
                    "Unhandled error while trying to fetch parkingposition data"
                )
        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch parkingposition, error: %s", error)
        return False

    async def getTripLast(self, vin):
        """Get car information like VIN, nickname, etc."""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/trips/{vin}/shortterm/last", ""
            )
            if "data" in response:
                return {"trip_last": response["data"]}

            if response.get("status_code", 0) in [404, 502]:
                _LOGGER.debug("No last trip data available for this vehicle")
            else:
                _LOGGER.warning(
                    "Could not fetch last trip data, server response: %s", response
                )

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch last trip data, error: %s", error)
        return False

    async def getTripRefuel(self, vin):
        """Get information about the trip since last refuel"""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/trips/{vin}/cyclic/last", ""
            )
            if "data" in response:
                return {"trip_refuel": response["data"]}

            if response.get("status_code", 0) in [404, 502]:
                _LOGGER.debug("No refuel trip data available for this vehicle")
            else:
                _LOGGER.warning(
                    "Could not fetch refuel trip data, server response: %s", response
                )

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch last trip data, error: %s", error)
        return False

    async def getTripLongterm(self, vin):
        """Get information about the trip last longterm"""
        if not await self.validate_tokens():
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/trips/{vin}/longterm/last", ""
            )
            if "data" in response:
                return {"trip_longterm": response["data"]}

            if response.get("status_code", 0) in [404, 502]:
                _LOGGER.debug("No longterm trip data available for this vehicle")
            else:
                _LOGGER.warning(
                    "Could not fetch longterm trip data, server response: %s", response
                )

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not fetch last trip data, error: %s", error)
        return False

    async def wakeUpVehicle(self, vin):
        """Wake up vehicle to send updated data to VW Backend."""
        if not await self.validate_tokens():
            return False
        try:
            return await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/vehiclewakeuptrigger",
                json={},
                return_raw=True,
            )

        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not refresh the data, error: %s", error)
        return False

    async def get_request_status(self, vin, requestId, actionId=""):
        """Return status of a request ID for a given section ID."""
        if self.logged_in is False:
            if not await self.doLogin():
                _LOGGER.warning("Login for %s account failed!", BRAND)
                raise AuthenticationError(f"Login for {BRAND} account failed")
        try:
            if not await self.validate_tokens():
                _LOGGER.info(
                    "Session expired. Initiating new login for %s account", BRAND
                )
                if not await self.doLogin():
                    _LOGGER.warning("Login for %s account failed!", BRAND)
                    raise AuthenticationError(f"Login for {BRAND} account failed")

            response = await self.getPendingRequests(vin)

            requests = response.get("data", [])
            result = None
            for request in requests:
                if request.get("id", "") == requestId:
                    result = request.get("status")

            # Translate status messages to meaningful info
            if result in ("in_progress", "queued", "fetched"):
                status = "In Progress"
            elif result in ("request_fail", "failed"):
                status = "Failed"
            elif result == "unfetched":
                status = "No response"
            elif result in ("request_successful", "successful"):
                status = "Success"
            elif result == "fail_ignition_on":
                status = "Failed because ignition is on"
            else:
                status = result
        except Exception as error:
            _LOGGER.warning("Failure during get request status: %s", error)
            raise RequestError(f"Failure during get request status: {error}") from error
        else:
            return status

    async def check_spin_state(self):
        """Determine SPIN state to prevent lockout due to wrong SPIN."""
        result = await self.get(f"{BASE_API}/vehicle/v1/spin/state")
        remainingTries = result.get("remainingTries", None)
        if remainingTries is None:
            raise SPINError("Couldn't determine S-PIN state")

        if remainingTries < 3:
            raise SPINError(
                "Remaining tries for S-PIN is < 3. Bailing out for security reasons. "
                "To resume operation, please make sure the correct S-PIN has been set in the integration "
                "and then use the correct S-PIN once via the Volkswagen app."
            )

        return True

    async def setClimater(self, vin, data, action):
        """Execute climatisation actions."""
        action = "start" if action else "stop"
        try:
            response_raw = await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/climatisation/{action}",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setClimater: {str(e)}") from e

    async def setClimaterSettings(self, vin, data):
        """Execute climatisation settings."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/climatisation/settings",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setClimaterSettings: {str(e)}") from e

    async def setAuxiliary(self, vin, data, action):
        """Execute auxiliary climatisation actions."""
        action = "start" if action else "stop"
        try:
            response_raw = await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/auxiliaryheating/{action}",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setAuxiliary: {str(e)}") from e

    async def setWindowHeater(self, vin, action):
        """Execute window heating actions."""
        action = "start" if action else "stop"
        try:
            response_raw = await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/windowheating/{action}",
                json={},
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setWindowHeater: {str(e)}") from e

    async def setCharging(self, vin, action):
        """Execute charging actions."""
        action = "start" if action else "stop"
        try:
            response_raw = await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/charging/{action}",
                json={},
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setCharging: {str(e)}") from e

    async def setChargingSettings(self, vin, data):
        """Execute charging actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/charging/settings",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setChargingSettings: {str(e)}") from e

    async def setChargingCareModeSettings(self, vin, data):
        """Execute battery care mode actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/charging/care/settings",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(
                f"Unknown error during setChargingCareModeSettings: {str(e)}"
            ) from e

    async def setReadinessBatterySupport(self, vin, data):
        """Execute readiness battery support actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/readiness/batterysupport",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(
                f"Unknown error during setReadinessBatterySupport: {str(e)}"
            ) from e

    async def setDepartureProfiles(self, vin, data):
        """Execute departure timers actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/departure/profiles",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(
                f"Unknown error during setDepartureProfiles: {str(e)}"
            ) from e

    async def setClimatisationTimers(self, vin, data):
        """Execute climatisation timers actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/climatisation/timers",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(
                f"Unknown error during setClimatisationTimers: {str(e)}"
            ) from e

    async def setAuxiliaryHeatingTimers(self, vin, data):
        """Execute auxiliary heating timers actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/auxiliaryheating/timers",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(
                f"Unknown error during setAuxiliaryHeatingTimers: {str(e)}"
            ) from e

    async def setDepartureTimers(self, vin, data):
        """Execute departure timers actions."""
        try:
            response_raw = await self.put(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/departure/timers",
                json=data,
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setDepartureTimers: {str(e)}") from e

    async def setLock(self, vin, lock, spin):
        """Remote lock and unlock actions."""
        await self.check_spin_state()
        action = "lock" if lock else "unlock"
        try:
            response_raw = await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/access/{action}",
                json={"spin": spin},
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setLock: {str(e)}") from e

    async def setHonkAndFlash(self, vin, position):
        """Remote Honk and Flash actions."""
        await self.check_spin_state()
        try:
            response_raw = await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/honkandflash",
                json={
                    "userPosition": {
                        "longitude": position["lng"],
                        "latitude": position["lat"],
                    },
                    "mode": "flash",
                    "duration_s": 15,
                },
                return_raw=True,
            )
            return await self._handle_action_result(response_raw)
        except Exception as e:
            raise APIError(f"Unknown error during setHonkAndFlash: {str(e)}") from e

    # Token handling #
    async def validate_tokens(self) -> bool:
        """Validate expiry of tokens."""
        try:
            idtoken = self._session_tokens["identity"]["id_token"]
            atoken = self._session_tokens["identity"]["access_token"]
        except KeyError as error:
            _LOGGER.warning("Token validation failed - missing token data: %s", error)
            return False
        id_exp = jwt.decode(
            idtoken,
            options={"verify_signature": False, "verify_aud": False},
            algorithms=JWT_ALGORITHMS,
        ).get("exp", None)
        at_exp = jwt.decode(
            atoken,
            options={"verify_signature": False, "verify_aud": False},
            algorithms=JWT_ALGORITHMS,
        ).get("exp", None)
        id_dt = datetime.fromtimestamp(int(id_exp))
        at_dt = datetime.fromtimestamp(int(at_exp))
        now = datetime.now()
        later = now + self._session_refresh_interval

        # Check if tokens have expired, or expires now
        if now >= id_dt or now >= at_dt:
            _LOGGER.debug("Tokens have expired. Try to fetch new tokens")
            if await self.refresh_tokens():
                _LOGGER.debug("Successfully refreshed tokens")
            else:
                return False
        # Check if tokens expires before next update
        elif later >= id_dt or later >= at_dt:
            _LOGGER.debug("Tokens about to expire. Try to fetch new tokens")
            if await self.refresh_tokens():
                _LOGGER.debug("Successfully refreshed tokens")
            else:
                return False
        return True

    async def refresh_tokens(self):
        """Refresh tokens."""
        try:
            tHeaders = {
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
                "x-android-package-name": ANDROID_PACKAGE_NAME,
            }

            body = {
                "grant_type": "refresh_token",
                "refresh_token": self._session_tokens["identity"]["refresh_token"],
                "client_id": CLIENT_ID,
            }
            response = await self._session.post(
                url=f"{BASE_API}/auth/v1/idk/oidc/token",
                headers=tHeaders,
                data=body,
            )
            await self.update_service_status("token", response.status)
            if response.status == 200:
                tokens = await response.json()

                if not tokens or "access_token" not in tokens:
                    _LOGGER.error("Invalid refresh token response: %s", tokens)
                    return False
                for token in tokens:
                    self._session_tokens["identity"][token] = tokens[token]
                self._session_headers["Authorization"] = (
                    "Bearer " + self._session_tokens["identity"]["access_token"]
                )
                _LOGGER.debug("Successfully refreshed and updated tokens")
            else:
                response_text = await response.text()
                _LOGGER.warning(
                    "Token refresh failed with status %s: %s",
                    response.status,
                    response_text,
                )
                return False
        except Exception as error:  # pylint: disable=broad-exception-caught
            _LOGGER.warning("Could not refresh tokens: %s", error)
            return False
        else:
            return True

    async def update_service_status(self, url, response_code):
        """Update service status."""
        if response_code in [200, 204, 207]:
            status = "Up"
        elif response_code == 401:
            status = "Unauthorized"
        elif response_code == 403:
            status = "Forbidden"
        elif response_code == 429:
            status = "Rate limited"
        elif response_code == 1000:
            status = "Error"
        else:
            status = "Down"

        if "vehicle/v2/vehicles" in url:
            self._service_status["vehicles"] = status
        elif "parkingposition" in url:
            self._service_status["parkingposition"] = status
        elif "/vehicle/v1/trips/" in url:
            self._service_status["trips"] = status
        elif "capabilities" in url:
            self._service_status["capabilities"] = status
        elif "selectivestatus" in url:
            self._service_status["selectivestatus"] = status
        elif "token" in url:
            self._service_status["token"] = status
        else:
            _LOGGER.debug('Unhandled API URL: "%s"', url)

    async def get_service_status(self):
        """Return list of service statuses."""
        _LOGGER.debug("Getting API status updates")
        return self._service_status

    # Class helpers #
    @property
    def vehicles(self):
        """Return list of Vehicle objects."""
        return self._vehicles

    @property
    def logged_in(self):
        """Return cached logged in state.

        Not actually checking anything.
        """
        return self._session_logged_in

    def vehicle(self, vin):
        """Return vehicle object for given vin."""
        return next(
            (
                vehicle
                for vehicle in self.vehicles
                if vehicle.unique_id.lower() == vin.lower()
            ),
            None,
        )

    def hash_spin(self, challenge, spin):
        """Convert SPIN and challenge to hash."""
        spinArray = bytearray.fromhex(spin)
        byteChallenge = bytearray.fromhex(challenge)
        spinArray.extend(byteChallenge)
        return hashlib.sha512(spinArray).hexdigest()

    async def validate_login(self) -> bool:
        """Check that we have a valid access token."""
        try:
            if not await self.validate_tokens():
                return False
        except OSError as error:
            _LOGGER.warning("Could not validate login: %s", error)
            return False
        else:
            return True


class vwid():

    # _LOGGER.setLevel(logging.DEBUG)
    connection = {}

    def __init__(self, session):
        self.session = session

    def set_vin(self, vin):
        self.vin = vin

    def set_credentials(self, username, password):
        self.username = username
        self.password = password

    def set_jobs(self, jobs):
        self.jobs_string = ','.join(jobs)

    async def get_status(self):
        # error codes SOCERR-xx raised:
        # SOCERR-00: general error
        # SOCERR-01: login problem, username, password wrong, account locked, etc.
        # SOCERR-02: vehicle not found in account, VIN wrong?
        try:
            async with ClientSession(headers={'Connection': 'keep-alive'}) as session:
                _now = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                data = {}
                data['charging'] = {}
                data['charging']['batteryStatus'] = {}
                data['charging']['batteryStatus']['value'] = {}
                data['charging']['batteryStatus']['value']['currentSOC_pct'] = str(0)
                data['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] = str(0)
                data['charging']['batteryStatus']['value']['carCapturedTimestamp'] = _now
                data['charging']['batteryStatus']['value']['odometer'] = None

                _k = str(vwid.connection.keys())
                _LOGGER.debug(f"libvwid.get_status connections at entry: vwid.connections.keys={_k}")
                _update_result = False
                if self.username not in vwid.connection:
                    _LOGGER.debug(f"create new connection, key={self.username}")
                    vwid.connection[self.username] = Connection(session, self.username, self.password)
                    self._connection = vwid.connection[self.username]
                    vwid.connection[self.username]._session_tokens['identity'] = {}
                    vwid.connection[self.username]._session_tokens['Legacy'] = {}
                    for token in self.tokens:
                        vwid.connection[self.username]._session_tokens['identity'][token] = self.tokens[token]
                        vwid.connection[self.username]._session_tokens['Legacy'][token] = self.tokens[token]
                    _conn_reuse = False
                else:
                    _LOGGER.debug(f"reuse existing connection, key={self.username}")
                    vwid.connection[self.username]._session = session
                    _conn_reuse = True
                if not _conn_reuse:
                    _doLogin_result = await vwid.connection[self.username].doLogin()
                    _LOGGER.debug("after 1st doLogin, result=" + str(_doLogin_result))
                    if _doLogin_result:
                        _update_result = True
                    else:
                        raise Exception(f"SOCERR-01: Login für User {self.username} fehlgeschlagen")
                else:
                    _update_result = await vwid.connection[self.username].update()
                    _LOGGER.debug("after 1st connection.update without doLogin, result=" + str(_update_result))
                    if not _update_result:
                        _doLogin_result = await vwid.connection[self.username].doLogin()
                        _LOGGER.debug("after 2nd doLogin, result=" + str(_doLogin_result))
                        if _doLogin_result:
                            _update_result = await vwid.connection[self.username].update()
                            _LOGGER.debug("after 2nd connection.update, result=" + str(_update_result))
                        else:
                            _LOGGER.error(f"retry doLogin for user {self.username} failed, exit")
                            raise Exception(f"SOCERR-01: Login für User {self.username} fehlgeschlagen")
                if _update_result:
                    _LOGGER.debug("update/doLogin look OK, get results")
                    for vehicle in vwid.connection[self.username].vehicles:
                        _LOGGER.debug("vehicle loop: " + str(vehicle) + ", self.vin=" + str(self.vin))
                        if str(vehicle) == str(self.vin):
                            _LOGGER.debug("vehicle loop match: " + str(vehicle) + ", self.vin=" + str(self.vin))
                            soc = vehicle._states['charging']['batteryStatus']['value']['currentSOC_pct']
                            range =\
                                vehicle._states['charging']['batteryStatus']['value']['cruisingRangeElectric_km']
                            ts = vehicle._states['charging']['batteryStatus']['value']['carCapturedTimestamp']
                            odometer = vehicle._states['measurements']['odometerStatus']['value']['odometer']
                            _LOGGER.debug("vehicle  =" + str(vehicle))
                            _LOGGER.debug("soc      =" + str(soc))
                            _LOGGER.debug("range    =" + str(range))
                            _LOGGER.debug("timestamp=" + str(ts))
                            tsxx = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
                            _LOGGER.debug("timestampxx=" + str(tsxx))
                            data['charging']['batteryStatus']['value']['currentSOC_pct'] = str(soc)
                            data['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] = str(range)
                            data['charging']['batteryStatus']['value']['carCapturedTimestamp'] = str(tsxx)
                            data['charging']['batteryStatus']['value']['odometer'] = str(odometer)
                            _LOGGER.debug("return data =" + to_json(data, indent=4))
                            for token in vwid.connection[self.username]._session_tokens['identity']:
                                self.tokens[token] =\
                                    vwid.connection[self.username]._session_tokens['identity'][token]
                            _LOGGER.info("VWID: soc=" + str(soc)+", range=" + str(range) + "@" + str(tsxx) +
                                         ', odometer=' + str(odometer))
                            return data
                    else:
                        _LOGGER.error(f"SOCERR-02: Fahrzeug mit VIN {self.vin} nicht gefunden")
                        raise Exception(f"SOCERR-02: Fahrzeug mit VIN {self.vin} nicht gefunden")
                else:
                    _t = f"SOCERR-00: Für User {self.username} und VIN {self.vin} wurden keine Daten empfangen."
                    _LOGGER.error(f"{_t}: get_status update failed")
                    raise Exception(_t)
        except Exception as e:
            _LOGGER.exception(f"get_status failed 0, exception={e}")
            # if exception is a SOCERR reraise it, otherwise raise general SOCERR-00
            if "SOCERR" in str(e):
                raise e
            else:
                _t = f"SOCERR-00: Für User {self.username} und VIN {self.vin} wurden keine Daten empfangen"
                raise Exception(f"{_t} {e}")
