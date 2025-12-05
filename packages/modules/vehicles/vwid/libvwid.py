#!/usr/bin/env python3
"""Communicate with Volkswagen Connect services."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import hashlib
from json import dumps as to_json
from json import loads
import logging
from random import randint, random
import re
from urllib.parse import parse_qs, urljoin, urlparse

import aiohttp
# from aiohttp.hdrs import METH_GET, METH_POST, METH_PUT
import bs4
import jwt

ANDROID_PACKAGE_NAME = "com.volkswagen.weconnect"
APP_URI = "weconnect://authenticated"
BASE_API = "https://emea.bff.cariad.digital"
BASE_AUTH = "https://identity.vwgroup.io"
BASE_SESSION = "https://msg.volkswagen.de"
BRAND = "VW"
USER_AGENT = "Volkswagen/3.51.1-android/14"
CLIENT = {
    "Legacy": {
        "CLIENT_ID": "a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com",
        "SCOPE": "openid profile badge cars dealers vin",
        "TOKEN_TYPES": "code",
    }
}
COUNTRY = "DE"
HEADERS_SESSION = {
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Accept-charset": "UTF-8",
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
    "tokentype": "IDK_TECHNICAL",
    "x-android-package-name": ANDROID_PACKAGE_NAME,
}
HEADERS_AUTH = {
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
              "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded",
    "x-android-package-name": ANDROID_PACKAGE_NAME,
}

MAX_RETRIES_ON_RATE_LIMIT = 3
TIMEOUT = timedelta(seconds=30)
JWT_ALGORITHMS = ["RS256"]


class Services:
    """Service names that are used in `capabilities` and `selectivestatus` calls."""

    CHARGING = "charging"
    PARAMETERS = "parameters"
    SERVICE_STATUS = "service_status"


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
                _LOGGER.warning("Access to %s has expired!", service)
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
        fulldebug=False,
        country=COUNTRY,
        interval=timedelta(minutes=5),
    ) -> None:
        """Initialize."""
        self._x_client_id = None
        self._session = session
        self._session_fulldebug = fulldebug
        self._session_headers = HEADERS_SESSION.copy()
        self._session_base = BASE_SESSION
        self._session_auth_headers = HEADERS_AUTH.copy()
        self._session_auth_base = BASE_AUTH
        self._session_refresh_interval = interval

        no_vin_key = ""
        self._session_auth_ref_urls = {no_vin_key: BASE_SESSION}
        self._session_spin_ref_urls = {no_vin_key: BASE_SESSION}
        self._session_logged_in = False
        self._session_first_update = False
        self._session_auth_username = username
        self._session_auth_password = password
        self._session_tokens = {}
        self._session_country = country.upper()

        self._vehicles = []

        _LOGGER.debug("Using service %s", self._session_base)

        self._jarCookie = ""
        self._state = {}

        self._service_status = {}

    def _clear_cookies(self):
        self._session._cookie_jar._cookies.clear()

    # API Login
    async def doLogin(self, tries: int = 3):
        """Login method, clean login."""
        async with self._login_lock:
            _LOGGER.debug("Initiating new login")

            for i in range(tries):
                self._session_logged_in = await self._login("Legacy")
                if self._session_logged_in:
                    break
                if i > tries:
                    _LOGGER.error("Login failed after %s tries", tries)
                    return False
                await asyncio.sleep(random() * 5)

            if not self._session_logged_in:
                return False

            _LOGGER.debug("Successfully logged in")
            self._session_tokens["identity"] = self._session_tokens["Legacy"].copy()

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

    async def get_openid_config(self):
        """Get OpenID config."""
        if self._session_fulldebug:
            _LOGGER.debug("Requesting openid config")
        req = await self._session.get(
            url=f"{BASE_API}/login/v1/idk/openid-configuration"
        )
        if req.status != 200:
            _LOGGER.error("Failed to get OpenID configuration, status: %s", req.status)
            raise Exception("OpenID configuration error")
        return await req.json()

    async def get_authorization_page(self, authorization_endpoint, client):
        """Get authorization page (login page)."""
        if self._session_fulldebug:
            _LOGGER.debug(
                'Requesting authorization page from "%s"', authorization_endpoint
            )
            self._session_auth_headers.pop("Referer", None)
            self._session_auth_headers.pop("Origin", None)
            _LOGGER.debug('Request headers: "%s"', self._session_auth_headers)

        try:
            req = await self._session.get(
                url=authorization_endpoint,
                headers=self._session_auth_headers,
                allow_redirects=False,
                params={
                    "redirect_uri": APP_URI,
                    "response_type": CLIENT[client].get("TOKEN_TYPES"),
                    "client_id": CLIENT[client].get("CLIENT_ID"),
                    "scope": CLIENT[client].get("SCOPE"),
                },
            )

            # Check if the response contains a redirect location
            location = req.headers.get("Location")
            if not location:
                raise Exception(
                    f"Missing 'Location' header, payload returned: {await req.content.read()}"
                )

            ref = urljoin(authorization_endpoint, location)
            if "error" in ref:
                parsed_query = parse_qs(urlparse(ref).query)
                error_msg = parsed_query.get("error", ["Unknown error"])[0]
                error_description = parsed_query.get(
                    "error_description", ["No description"]
                )[0]
                _LOGGER.exception("Authorization error: %s", error_description)
                raise Exception(error_msg)

            # If redirected, fetch the new location
            req = await self._session.get(
                url=ref, headers=self._session_auth_headers, allow_redirects=False
            )

            if req.status != 200:
                raise Exception("Failed to fetch authorization endpoint")

            return await req.text()

        except Exception as e:
            _LOGGER.warning("Error during fetching authorization page: %s", str(e))
            raise

    def extract_form_data(self, page_content, form_id):
        """Extract form data from a page."""
        soup = bs4.BeautifulSoup(page_content, "html.parser")
        form = soup.find("form", id=form_id)
        if form is None:
            _LOGGER.debug(f"Form with ID '{form_id}' not found.")
            return None
        return {
            input_field["name"]: input_field["value"]
            for input_field in form.find_all("input", type="hidden")
        }

    def extract_state_token(self, page_content):
        """Extract state token from a page."""
        soup = bs4.BeautifulSoup(page_content, "html.parser")
        state_input = soup.select_one('input[name="state"]')
        if not state_input or not state_input.get("value"):
            _LOGGER.debug("State token not found.")
            return None
        return state_input["value"]

    def extract_password_form_data(self, soup):
        """Extract password form data from a page."""
        pw_form = {}
        for script in soup.find_all("script"):
            if "src" in script.attrs or not script.string:
                continue
            script_text = script.string

            if "window._IDK" not in script_text:
                continue  # Skip scripts that don't contain relevant data
            if re.match('"errorCode":"', script_text):
                raise Exception("Error code found in script data.")

            pw_form["relayState"] = re.search(
                '"relayState":"([a-f0-9]*)"', script_text
            )[1]
            pw_form["hmac"] = re.search('"hmac":"([a-f0-9]*)"', script_text)[1]
            pw_form["email"] = re.search('"email":"([^"]*)"', script_text)[1]
            pw_form["_csrf"] = re.search("csrf_token:\\s*'([^\"']*)'", script_text)[1]

            post_action = re.search('"postAction":\\s*"([^"\']*)"', script_text)[1]
            client_id = re.search('"clientId":\\s*"([^"\']*)"', script_text)[1]
            return pw_form, post_action, client_id

        raise Exception("Password form data not found in script.")

    async def post_form(self, session, url, headers, form_data, redirect=True):
        """Post a form and check for success."""
        req = await session.post(
            url, headers=headers, data=form_data, allow_redirects=redirect
        )
        if not redirect and req.status == 302:
            return req.headers["Location"]
        if req.status != 200:
            raise Exception("Form POST request failed.")
        return await req.text()

    async def handle_login_with_password(self, session, url, auth_headers, form_data):
        """Handle login with email and password."""
        return await self.post_form(session, url, auth_headers, form_data, False)

    async def follow_redirects(self, session, pw_url, redirect_location):
        """Handle redirects."""
        ref = urljoin(pw_url, redirect_location)
        max_depth = 10
        while not ref.startswith(APP_URI):
            if max_depth == 0:
                raise Exception("Too many redirects")
            response = await session.get(
                url=ref, headers=self._session_auth_headers, allow_redirects=False
            )
            if "Location" not in response.headers:
                _LOGGER.warning("Failed to find next redirect location")
                raise Exception("Redirect error")
            ref = urljoin(ref, response.headers["Location"])
            max_depth -= 1
        return ref

    async def _login(self, client="Legacy"):
        """Login function."""

        try:
            # Clear cookies and reset headers
            self._clear_cookies()
            self._session_headers = HEADERS_SESSION.copy()
            self._session_auth_headers = HEADERS_AUTH.copy()

            # Get OpenID configuration
            openid_config = await self.get_openid_config()
            authorization_endpoint = openid_config["authorization_endpoint"]
            token_endpoint = openid_config["token_endpoint"]
            auth_issuer = openid_config["issuer"]

            # Get authorization page
            authorization_page = await self.get_authorization_page(
                authorization_endpoint, client
            )

            # Extract form data
            mailform = self.extract_form_data(authorization_page, "emailPasswordForm")
            state_token = self.extract_state_token(authorization_page)
            if mailform:
                _LOGGER.debug("Legacy authentication found., client=" + str(client))
                mailform["email"] = self._session_auth_username
                pe_url = auth_issuer + bs4.BeautifulSoup(
                    authorization_page, "html.parser"
                ).find("form", id="emailPasswordForm").get("action")

                # POST email
                # https://identity.vwgroup.io/signin-service/v1/{CLIENT_ID}/login/identifier
                self._session_auth_headers["Referer"] = authorization_endpoint
                self._session_auth_headers["Origin"] = auth_issuer
                response_text = await self.post_form(
                    self._session, pe_url, self._session_auth_headers, mailform
                )

                # Extract password form data
                response_soup = bs4.BeautifulSoup(response_text, "html.parser")
                pw_form, post_action, client_id = self.extract_password_form_data(
                    response_soup
                )

                # Add password to form data
                pw_form["password"] = self._session_auth_password
                pw_url = f"{auth_issuer}/signin-service/v1/{client_id}/{post_action}"

                # POST password
                self._session_auth_headers["Referer"] = pe_url
                redirect_location = await self.handle_login_with_password(
                    self._session, pw_url, self._session_auth_headers, pw_form
                )

                # Handle redirects and extract tokens
                redirect_response = await self.follow_redirects(
                    self._session, pw_url, redirect_location
                )
                jwt_auth_code = parse_qs(urlparse(redirect_response).query)["code"][0]
            elif state_token:
                _LOGGER.debug(
                    "Legacy authentication not found. Trying new authentication flow., client=" + str(client)
                )

                # Do login
                login_form = {}
                login_form["username"] = self._session_auth_username
                login_form["password"] = self._session_auth_password
                login_form["state"] = state_token
                login_url = f"{auth_issuer}/u/login?state={state_token}"

                redirect_location = await self.post_form(
                    self._session,
                    login_url,
                    self._session_auth_headers,
                    login_form,
                    False,
                )

                # Handle redirects and extract tokens
                redirect_response = await self.follow_redirects(
                    self._session, auth_issuer, redirect_location
                )
                jwt_auth_code = parse_qs(urlparse(redirect_response).query)["code"][0]
            else:
                _LOGGER.error(
                    "Unable to find valid login page."
                    "Try logging in to the portal: https://www.myvolkswagen.net/"
                )
                return False

            # Exchange authorization code for tokens
            token_body = {
                "client_id": CLIENT[client].get("CLIENT_ID"),
                "grant_type": "authorization_code",
                "code": jwt_auth_code,
                "redirect_uri": APP_URI,
            }

            # Token endpoint
            token_response = await self.post_form(
                self._session, token_endpoint, self._session_auth_headers, token_body
            )

            # Store session tokens
            self._session_tokens[client] = json_loads(token_response)

            # Verify tokens
            if not await self.verify_tokens(
                self._session_tokens[client].get("id_token", ""), "identity"
            ):
                _LOGGER.warning("User identity token could not be verified!")
            else:
                _LOGGER.debug("User identity token verified successfully, client=" + str(client))

            # Mark session as logged in
            self._session_logged_in = True

        except Exception as error:
            _LOGGER.error("Login failed: %s", error)
            self._session_logged_in = False
            return False
        self._session_headers["Authorization"] = (
            "Bearer " + self._session_tokens[client]["access_token"]
        )
        return True

    async def _handle_action_result(self, response_raw):
        response = await response_raw.json(loads=json_loads)
        if not response:
            raise Exception("Invalid or no response")
        if response == 429:
            return {"id": None, "state": "Throttled"}
        request_id = response.get("data", {}).get("requestID", 0)
        _LOGGER.debug("Request returned with request id: %s", request_id)
        return {"id": str(request_id)}

    async def terminate(self):
        """Log out from connect services."""
        _LOGGER.debug("Initiating logout")
        await self.logout()

    async def logout(self):
        """Logout, revoke tokens."""
        _LOGGER.debug("logout - revoke token")
        self._session_headers.pop("Authorization", None)

        if self._session_logged_in:
            if self._session_headers.get("identity", {}).get("identity_token"):
                _LOGGER.debug("Revoking Identity Access Token")

            if self._session_headers.get("identity", {}).get("refresh_token"):
                _LOGGER.debug("Revoking Identity Refresh Token")
                params = {"token": self._session_tokens["identity"]["refresh_token"]}
                await self.post(
                    "https://emea.bff.cariad.digital/login/v1/idk/revoke", data=params
                )

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
                timeout=aiohttp.ClientTimeout(total=TIMEOUT.seconds),
                cookies=self._jarCookie,
                raise_for_status=False,
                **kwargs,
            ) as response:
                response.raise_for_status()

                # Update cookie jar
                if self._jarCookie != "":
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
                    elif response.status >= 200 or response.status <= 300:
                        res = await response.json(loads=json_loads)
                    else:
                        res = {}
                        _LOGGER.debug(
                            "Not success status code [%s] response: %s",
                            response.status,
                            response.text,
                        )
                except Exception:
                    res = {}
                    _LOGGER.debug(
                        "Something went wrong [%s] response: %s",
                        response.status,
                        response.text,
                    )
                    if return_raw:
                        return response
                    return res

                if self._session_fulldebug:
                    _LOGGER.debug(
                        'Request for "%s" returned with status code [%s], headers: %s, response: %s',
                        url,
                        response.status,
                        response.headers,
                        res,
                    )
                else:
                    _LOGGER.debug(
                        'Request for "%s" returned with status code [%s]',
                        url,
                        response.status,
                    )

                if return_raw:
                    res = response
                return res
        except aiohttp.client_exceptions.ClientResponseError as httperror:
            # Update service status
            await self.update_service_status(url, httperror.code)
            raise httperror from None
        except Exception as error:
            # Update service status
            await self.update_service_status(url, 1000)
            raise error from None

    async def get(self, url, vin="", tries=0):
        """Perform a get query."""
        try:
            return await self._request(aiohttp.hdrs.METH_GET, url)
        except aiohttp.client_exceptions.ClientResponseError as error:
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
                _LOGGER.warning(
                    "Got HTTP 500 from server, service might be temporarily unavailable"
                )
            elif error.status == 502:
                _LOGGER.warning(
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
                    aiohttp.hdrs.METH_POST, url, return_raw=return_raw, **data
                )
            return await self._request(aiohttp.hdrs.METH_POST, url, return_raw=return_raw)
        except aiohttp.client_exceptions.ClientResponseError as error:
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
                return await self._request(aiohttp.hdrs.METH_PUT, url, return_raw=return_raw, **data)
            return await self._request(aiohttp.hdrs.METH_PUT, url, return_raw=return_raw)
        except aiohttp.client_exceptions.ClientResponseError as error:
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
            if not await self.validate_tokens:
                _LOGGER.warning(
                    "Session expired. Initiating new login for %s account", BRAND
                )
                if not await self.doLogin():
                    _LOGGER.warning("Login for %s account failed!", BRAND)
                    raise Exception(f"Login for {BRAND} account failed")
            else:
                _LOGGER.debug("Going to call vehicle updates")
                # Get all Vehicle objects and update in parallell
                updatelist = [vehicle.update() for vehicle in self.vehicles]
                # Wait for all data updates to complete
                await asyncio.gather(*updatelist)

                return True
        except (OSError, LookupError, Exception) as error:
            _LOGGER.warning("Could not update information: %s", error)
        return False

    async def getPendingRequests(self, vin):
        """Get status information for pending requests."""
        if not await self.validate_tokens:
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/pendingrequests"
            )

            if response:
                response["refreshTimestamp"] = datetime.now(UTC)
                return response

        except Exception as error:
            _LOGGER.warning(
                "Could not fetch information for pending requests, error: %s", error
            )
        return False

    async def getOperationList(self, vin):
        """Collect operationlist for VIN, supported/licensed functions."""
        if not await self.validate_tokens:
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
                _LOGGER.warning("Could not fetch operation list: %s", response)
                data = {"error": "unknown"}
        except Exception as error:
            _LOGGER.warning("Could not fetch operation list, error: %s", error)
            data = {"error": "unknown"}
        return data

    async def getSelectiveStatus(self, vin, services):
        """Get status information for specified services."""
        if not await self.validate_tokens:
            return False
        try:
            response = await self.get(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/selectivestatus?jobs={','.join(services)}",
                "",
            )

            for service in services:
                if not response.get(service):
                    _LOGGER.debug(
                        "Did not receive return data for requested service %s."
                        " (This is expected for several service/car combinations)",
                        service,
                    )

            if response:
                response.update({"refreshTimestamp": datetime.now(UTC)})
                return response

        except Exception as error:
            _LOGGER.warning("Could not fetch selectivestatus, error: %s", error)
        return False

    async def getVehicleData(self, vin):
        """Get car information like VIN, nickname, etc."""
        if not await self.validate_tokens:
            return False
        try:
            response = await self.get(f"{BASE_API}/vehicle/v2/vehicles", "")

            for vehicle in response.get("data"):
                if vehicle.get("vin") == vin:
                    return {"vehicle": vehicle}

            _LOGGER.warning("Could not fetch vehicle data for vin %s", vin)

        except Exception as error:
            _LOGGER.warning("Could not fetch vehicle data, error: %s", error)
        return False

    async def wakeUpVehicle(self, vin):
        """Wake up vehicle to send updated data to VW Backend."""
        if not await self.validate_tokens:
            return False
        try:
            return await self.post(
                f"{BASE_API}/vehicle/v1/vehicles/{vin}/vehiclewakeuptrigger",
                json={},
                return_raw=True,
            )

        except Exception as error:
            _LOGGER.warning("Could not refresh the data, error: %s", error)
        return False

    async def get_request_status(self, vin, requestId, actionId=""):
        """Return status of a request ID for a given section ID."""
        if self.logged_in is False:
            if not await self.doLogin():
                _LOGGER.warning("Login for %s account failed!", BRAND)
                raise Exception(f"Login for {BRAND} account failed")
        try:
            if not await self.validate_tokens:
                _LOGGER.warning(
                    "Session expired. Initiating new login for %s account", BRAND
                )
                if not await self.doLogin():
                    _LOGGER.warning("Login for %s account failed!", BRAND)
                    raise Exception(f"Login for {BRAND} account failed")

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
            raise Exception(f"Failure during get request status: {error}") from error
        else:
            return status

    async def check_spin_state(self):
        """Determine SPIN state to prevent lockout due to wrong SPIN."""
        result = await self.get(f"{BASE_API}/vehicle/v1/spin/state")
        remainingTries = result.get("remainingTries", None)
        if remainingTries is None:
            raise Exception("Couldn't determine S-PIN state.")

        if remainingTries < 3:
            raise Exception(
                "Remaining tries for S-PIN is < 3. Bailing out for security reasons. "
                "To resume operation, please make sure the correct S-PIN has been set in the integration "
                "and then use the correct S-PIN once via the Volkswagen app."
            )

        return True

    # Token handling #
    @property
    async def validate_tokens(self):
        """Validate expiry of tokens."""
        _LOGGER.debug("validate_tokens")
        idtoken = self._session_tokens["identity"]["id_token"]
        atoken = self._session_tokens["identity"]["access_token"]
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
            _LOGGER.warning("Tokens have expired. Try to fetch new tokens")
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

    async def verify_tokens(self, token, type, client="Legacy"):
        """Verify JWT against JWK(s)."""
        _LOGGER.debug("verify_tokens, type=" + str(type) + ", client=" + str(client))
        if type == "identity":
            req = await self._session.get(url="https://identity.vwgroup.io/v1/jwks")
            keys = await req.json()
            audience = [
                CLIENT[client].get("CLIENT_ID"),
                "VWGMBB01DELIV1",
                "https://api.vas.eu.dp15.vwg-connect.com",
                "https://api.vas.eu.wcardp.io",
            ]
        else:
            _LOGGER.debug("Not implemented")
            return False
        try:
            pubkeys = {}
            for jwk in keys["keys"]:
                kid = jwk["kid"]
                if jwk["kty"] == "RSA":
                    pubkeys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(to_json(jwk))

            token_kid = jwt.get_unverified_header(token)["kid"]

            pubkey = pubkeys[token_kid]
            jwt.decode(token, key=pubkey, algorithms=JWT_ALGORITHMS, audience=audience)
        except Exception as error:
            _LOGGER.exception("Failed to verify token, error: %s", error)
            return False
        return True

    async def refresh_tokens(self):
        """Refresh tokens."""
        _LOGGER.debug("refresh_tokens")
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
                "client_id": CLIENT["Legacy"]["CLIENT_ID"],
            }
            response = await self._session.post(
                url="https://emea.bff.cariad.digital/login/v1/idk/token",
                headers=tHeaders,
                data=body,
            )
            await self.update_service_status("token", response.status)
            if response.status == 200:
                tokens = await response.json()
                # Verify Token
                if not await self.verify_tokens(tokens["id_token"], "identity"):
                    _LOGGER.warning("Token could not be verified!")
                _LOGGER.debug("refresh_tokens successful")
                for token in tokens:
                    self._session_tokens["identity"][token] = tokens[token]
                self._session_headers["Authorization"] = (
                    "Bearer " + self._session_tokens["identity"]["access_token"]
                )
            else:
                _LOGGER.warning(
                    "Something went wrong when refreshing %s account tokens", BRAND
                )
                return False
        except Exception as error:
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

    @property
    async def validate_login(self):
        """Check that we have a valid access token."""
        try:
            if not await self.validate_tokens:
                return False
        except OSError as error:
            _LOGGER.warning("Could not validate login: %s", error)
            return False
        else:
            return True


class vwid():

    connection = {}

    def __init__(self, session):
        self.session = session
        # self.log = logging.getLogger(__name__)
        # self.connection = {}

    def set_vin(self, vin):
        self.vin = vin

    def set_credentials(self, username, password):
        self.username = username
        self.password = password

    def set_jobs(self, jobs):
        self.jobs_string = ','.join(jobs)

    async def get_status(self):
        try:
            async with aiohttp.ClientSession(headers={'Connection': 'keep-alive'}) as session:
                _now = datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                data = {}
                data['charging'] = {}
                data['charging']['batteryStatus'] = {}
                data['charging']['batteryStatus']['value'] = {}
                data['charging']['batteryStatus']['value']['currentSOC_pct'] = str(0)
                data['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] = str(0)
                data['charging']['batteryStatus']['value']['carCapturedTimestamp'] = _now

                try:
                    _k = str(vwid.connection.keys())
                    _LOGGER.info(f"libvwid.get_status connections at entry: vwid.connections.keys={_k}")
                    if self.username not in vwid.connection:
                        _LOGGER.info(f"create new connection, key={self.username}")
                        vwid.connection[self.username] = Connection(session, self.username, self.password)
                        self._connection = vwid.connection[self.username]
                        vwid.connection[self.username]._session_tokens['identity'] = {}
                        vwid.connection[self.username]._session_tokens['Legacy'] = {}
                        for token in self.tokens:
                            vwid.connection[self.username]._session_tokens['identity'][token] = self.tokens[token]
                            vwid.connection[self.username]._session_tokens['Legacy'][token] = self.tokens[token]
                        _conn_reuse = False
                    else:
                        _LOGGER.info(f"reuse existing connection, key={self.username}")
                        vwid.connection[self.username]._session = session
                        _conn_reuse = True
                    if not _conn_reuse:
                        _doLogin_result = await vwid.connection[self.username].doLogin()
                        _LOGGER.debug("after 1st doLogin, result=" + str(_doLogin_result))
                        if _doLogin_result:
                            _update_result = True
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
                                _LOGGER.error("retry doLogin failed, exit")
                                raise Exception("Login failed")
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
                                _LOGGER.debug("vehicle  =" + str(vehicle))
                                _LOGGER.debug("soc      =" + str(soc))
                                _LOGGER.debug("range    =" + str(range))
                                _LOGGER.debug("timestamp=" + str(ts))
                                tsxx = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
                                _LOGGER.debug("timestampxx=" + str(tsxx))
                                data['charging']['batteryStatus']['value']['currentSOC_pct'] = str(soc)
                                data['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] = str(range)
                                data['charging']['batteryStatus']['value']['carCapturedTimestamp'] = str(tsxx)
                                _LOGGER.debug("return data =" + to_json(data, indent=4))
                                for token in vwid.connection[self.username]._session_tokens['identity']:
                                    self.tokens[token] =\
                                        vwid.connection[self.username]._session_tokens['identity'][token]
                                return data
                    else:
                        _LOGGER.error("get_status rsp. update failed, raise exception")
                        raise Exception("get_status: keine Daten empfangen")
                except Exception as error:
                    _LOGGER.exception("get_status failed 1, raise exception, exception=" + str(error))
                    raise Exception(error)
        except Exception as error:
            _LOGGER.exception("get_status failed 0, raise exception=" + str(error))
            raise Exception(error)
