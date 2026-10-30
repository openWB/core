"""Synchronous VW EU Data Act login and dataset downloads."""

import io
import json
import re
import zipfile
from html.parser import HTMLParser
from typing import Optional, Union
from urllib.parse import urlencode, urljoin, urlparse

from requests import HTTPError, RequestException, Response, Session

BASE_URL = "https://eu-data-act.drivesomethinggreater.com"
OIDC_AUTHORIZE_URL = "https://identity.vwgroup.io/oidc/v1/authorize"
CALLBACK_LOGIN_PATH = "/services/callbacklogin"
METADATA_PATH = "/proxy_api/euda-apim/datarequest/vehicles/{vin}/metadata/partial"
LIST_PATH = "/proxy_api/euda-apim/datadelivery/vehicles/{vin}/{identifier}/list"
DOWNLOAD_PATH = "/proxy_api/euda-apim/datadelivery/vehicles/{vin}/{identifier}/download"
NO_CONTENT_SUFFIX = "_no_content_found.zip"
HTTP_TIMEOUT = (5, 15)
USER_AGENT = "vw_eu_data_act/0.3.3"

# OIDC client ID and portal brand state. SEAT and CUPRA share a client ID.
BRANDS = {
    "volkswagen": ("9b58543e-1c15-4193-91d5-8a14145bebb0@apps_vw-dilab_com", "VOLKSWAGEN_PASSENGER_CARS"),
    "audi": ("cc29b87a-5e9a-4362-aecf-5adea6b01bbb@apps_vw-dilab_com", "AUDI"),
    "skoda": ("3ea88bf9-1d4e-4a68-b3ad-4098c1f1d246@apps_vw-dilab_com", "SKODA"),
    "seat": ("f85e5b69-e3b2-43aa-9c0d-1b7d0e0b576f@apps_vw-dilab_com", "SEAT"),
    "cupra": ("f85e5b69-e3b2-43aa-9c0d-1b7d0e0b576f@apps_vw-dilab_com", "CUPRA"),
}
BRAND_PREFIXES = {
    "audi": ("WAU", "WA1", "WUA", "WU1", "99A", "AAA", "TRU"),
    "skoda": ("NAD", "TMB", "Y6U"),
    "cupra": ("VSS",),  # SEAT/CUPRA cannot be distinguished by this prefix.
}


def brand_for_vin(vin: str) -> str:
    return next((brand for brand, prefixes in BRAND_PREFIXES.items() if vin[:3] in prefixes), "volkswagen")


class ApiError(Exception):
    """Portal/network failure, with HTTP status when available."""

    def __init__(self, message: str, *, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.status = status


class AuthError(ApiError):
    """Login failed or the identity provider's form changed."""


class DatasetError(ApiError):
    """Malformed archive; it must not prevent processing newer datasets."""


class _LoginForm(HTMLParser):
    """Collect the first HTML form and its input fields."""

    def __init__(self, html: str) -> None:
        super().__init__()
        self.action = None
        self.fields = {}
        self._inside = False
        self._done = False
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attrs = dict(attrs)
        if tag == "form" and not self._done and not self._inside:
            self.action = attrs.get("action")
            self._inside = True
        elif tag == "input" and self._inside and attrs.get("name"):
            self.fields[attrs["name"]] = attrs.get("value") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._inside:
            self._inside, self._done = False, True


def _template_model(html: str) -> dict:
    # raw_decode also handles braces inside JSON strings, unlike brace counting.
    index = html.find("templateModel")
    start = html.find("{", index) if index >= 0 else -1
    try:
        return json.JSONDecoder().raw_decode(html[start:])[0] if start >= 0 else {}
    except ValueError:
        return {}


def _login_error(html: str) -> Optional[str]:
    model = _template_model(html)
    error = model.get("error") or model.get("errorCode")
    if isinstance(error, dict):
        return error.get("text") or error.get("errorCode") or str(error)
    return str(error) if error else None


def _is_universal_login(fields: dict) -> bool:
    return {"state", "username", "password"} <= fields.keys() and "hmac" not in fields


def _login_fields(html: str) -> tuple[dict, Optional[str]]:
    form = _LoginForm(html)
    model = _template_model(html)
    for key in ("hmac", "relayState"):
        if model.get(key):
            form.fields[key] = model[key]
    csrf = re.search(r"csrf_token\s*[:=]\s*['\"]([^'\"]+)['\"]", html)
    if csrf:
        form.fields.setdefault("_csrf", csrf.group(1))
    if not _is_universal_login(form.fields) and not all(key in form.fields for key in ("hmac", "_csrf")):
        raise AuthError(_login_error(html) or "Could not parse identity login form")
    return form.fields, form.action


def _check_login_status(response: Response) -> None:
    status = response.status_code
    if status >= 500 or status in (404, 429):
        raise ApiError(f"Identity provider error (HTTP {status})", status=status)
    if status >= 400:
        message = "Login failed - check email and password" if "/u/login" in urlparse(response.url).path else None
        raise AuthError(_login_error(response.text) or message or f"Login rejected (HTTP {status})")


class EudaApiClient:
    """The synchronous caller owns and closes the session."""

    def __init__(self, session: Session, email: str, password: str, brand: str = "volkswagen") -> None:
        self._session = session
        self._email, self._password, self._brand = email, password, brand
        self._logged_in = False

    def _request(self, method: str, url: str, **kwargs) -> Response:
        headers = {"User-Agent": USER_AGENT, **kwargs.pop("headers", {})}
        try:
            return self._session.request(method, url, headers=headers, timeout=HTTP_TIMEOUT, **kwargs)
        except HTTPError as error:
            # req.get_http_session() raises in its response hook. Keep the full
            # response for VW login status handling and the 401/403 retry below.
            if error.response is None:
                raise ApiError(f"HTTP error during {method}: {error}") from error
            return error.response
        except RequestException as error:
            raise ApiError(f"Network error during {method}: {error}") from error

    @staticmethod
    def _build_authorize_url(brand: str = "volkswagen") -> str:
        client_id, state = BRANDS.get(brand, BRANDS["volkswagen"])
        # The portal's redirect/authentication servlet fails for non-browser clients.
        return OIDC_AUTHORIZE_URL + "?" + urlencode({
            "client_id": client_id, "state": f"de__en__{state}", "response_type": "code",
            "scope": "openid cars profile", "redirect_uri": BASE_URL + "/login", "prompt": "login",
        })

    def _post_login_form(self, url: str, *, data: dict, referer: str) -> Response:
        """Follow at most ten redirects, stopping at the session-setting callback."""
        response = self._request("POST", url, data=data, headers={"Referer": referer}, allow_redirects=False)
        for hop in range(11):
            location = response.headers.get("Location")
            parsed = urlparse(response.url)
            callback = parsed.netloc == urlparse(BASE_URL).netloc and parsed.path.startswith(CALLBACK_LOGIN_PATH)
            if callback or response.status_code not in (301, 302, 303) or not location:
                return response
            previous_url = response.url
            next_url = urljoin(previous_url, location)
            response.close()
            if hop == 10:
                raise ApiError("Login redirect chain exceeded 10 hops")
            response = self._request("GET", next_url, headers={"Referer": previous_url}, allow_redirects=False)

    def login(self) -> None:
        """Authorize → legacy two-step or Auth0 single-form login → portal callback."""
        self._logged_in = False
        with self._request("GET", self._build_authorize_url(self._brand)) as response:
            _check_login_status(response)
            signin_url = response.url
            fields, action = _login_fields(response.text)

        if _is_universal_login(fields):
            # Auth0 posts both credentials at once; keep ?state= in the URL.
            fields.update(username=self._email, password=self._password, action="default")
            action_url = urljoin(signin_url, action or "")
            referer = signin_url
        else:
            fields["email"] = self._email
            with self._request("POST", urljoin(signin_url, action or ""), data=fields,
                               headers={"Referer": signin_url}) as response:
                _check_login_status(response)
                referer = response.url
                fields, action = _login_fields(response.text)

            fields.update(email=self._email, password=self._password)
            # Legacy relayState belongs in the POST body, not in the URL as well.
            action_url = urljoin(referer, action) if action else referer.split("?", 1)[0]

        with self._post_login_form(action_url, data=fields, referer=referer) as response:
            _check_login_status(response)
            parsed = urlparse(response.url)
            if parsed.netloc != urlparse(BASE_URL).netloc or not parsed.path.startswith(CALLBACK_LOGIN_PATH):
                if "/u/login" in parsed.path:
                    raise AuthError(_login_error(response.text) or "Login failed - check email and password")
                raise AuthError(_login_error(response.text) or "Login did not reach the portal callback")
            if not response.cookies.get("access_token"):
                raise AuthError("Login callback did not establish a session (access_token cookie missing)")
        self._logged_in = True

    def _authenticated_get(self, url: str, headers: Optional[dict] = None) -> Response:
        """Share the same one-time reauthentication for JSON and ZIP requests."""
        if not self._logged_in:
            self.login()
        for attempt in range(2):
            response = self._request("GET", url, headers=headers or {})
            status = response.status_code
            if status in (401, 403) and attempt == 0:
                response.close()
                self.login()
                continue
            if status >= 400:
                response.close()
                raise ApiError(f"Portal request failed (HTTP {status})", status=status)
            return response

    def _get_json(self, url: str, headers: Optional[dict] = None) -> Union[dict, list]:
        with self._authenticated_get(url, headers) as response:
            try:
                return response.json()
            except ValueError as error:
                raise ApiError("Invalid JSON from portal") from error

    def get_metadata(self, vin: str) -> dict:
        return self._get_json(BASE_URL + METADATA_PATH.format(vin=vin))

    def list_datasets(self, vin: str, identifier: str) -> list[dict]:
        url = BASE_URL + LIST_PATH.format(vin=vin, identifier=identifier)
        # The endpoint returns HTTP 500 without the matching request type.
        data = self._get_json(url, headers={"type": "partial"})
        return data if isinstance(data, list) else data.get("files", [])

    def download_dataset(self, vin: str, identifier: str, name: str) -> tuple[str, dict]:
        url = BASE_URL + DOWNLOAD_PATH.format(vin=vin, identifier=identifier)
        with self._authenticated_get(url, {"filename": name, "type": "partial"}) as response:
            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                    member = next((name for name in archive.namelist() if name.lower().endswith(".json")), None)
                    if member is None:
                        raise DatasetError("No JSON inside downloaded dataset")
                    data = json.loads(archive.read(member).decode("utf-8"))
            except (zipfile.BadZipFile, ValueError) as error:
                raise DatasetError("Could not read downloaded dataset") from error
        return name.removesuffix(".zip") + ".json", data
