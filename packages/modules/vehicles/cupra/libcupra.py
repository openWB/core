# A Python class to communicate with the "Cupra Connect" API.
# Adapted the libvwid.py module to cupra interface

import secrets
import logging
import json
import uuid
import base64
import hashlib

from datetime import datetime, timezone
from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    import lxml.html

# Constants
LOGIN_BASE = "https://identity.vwgroup.io/oidc/v1"
LOGIN_HANDLER_BASE = "https://identity.vwgroup.io"
API_BASE = "https://ola.prod.code.seat.cloud.vwgroup.com"
CLIENT_ID = "3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com"
USER_AGENT = "OLACupra/2.16.0 (Android 14; Pixel 8; Google) Mobile"


class cupra:
    def __init__(self, session):
        self.session = session
        self.headers = {}
        self.log = logging.getLogger(__name__)
        self.jobs_string = 'all'

    def form_from_response(self, text):
        page = lxml.html.fromstring(text)
        elements = page.xpath('//form//input[@type="hidden"]')
        form = {x.attrib['name']: x.attrib['value'] for x in elements}
        return (form, page.forms[0].action)

    def password_form(self, text):
        page = lxml.html.fromstring(text)
        elements = page.xpath('//script')

        # Todo: Find more elegant way parse this...
        objects = {}
        for a in elements:
            if (a.text) and (a.text.find('window._IDK') != -1):
                text = a.text.strip()
                text = text[text.find('\n'):text.rfind('\n')].strip()
                for line in text.split('\n'):
                    try:
                        (name, val) = line.strip().split(':', 1)
                    except ValueError:
                        continue
                    val = val.strip('\', ')
                    objects[name] = val

        json_model = json.loads(objects['templateModel'])

        if ('errorCode' in json_model):
            self.log.error("Login error: %s", json_model['errorCode'])
            return False

        try:
            # Generate form
            form = {}
            form['relayState'] = json_model['relayState']
            form['hmac'] = json_model['hmac']
            form['email'] = json_model['emailPasswordForm']['email']
            form['_csrf'] = objects['csrf_token']

            # Generate URL action
            action = '/signin-service/v1/%s/%s'\
                % (json_model['clientLegalEntityModel']['clientId'], json_model['postAction'])

            return (form, action)

        except KeyError:
            self.log.exception("Missing fields in response from Cupra API")
            return False

    def set_vin(self, vin):
        self.vin = vin

    def set_credentials(self, username, password):
        self.username = username
        self.password = password

    def set_jobs(self, jobs):
        self.jobs_string = ','.join(jobs)

    def get_code_challenge(self):
        code_verifier = secrets.token_urlsafe(64).replace('+', '-').replace('/', '_').replace('=', '')
        code_challenge = base64.b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest())
        code_challenge = code_challenge.decode('utf-8').replace('+', '-').replace('/', '_').replace('=', '')
        return (code_verifier, code_challenge)

    def convert_to_camel_case(self, json):
        def to_camel_case(s):
            parts = s.split('_')
            return parts[0] + ''.join(word.capitalize() for word in parts[1:])

        return {to_camel_case(k): v for k, v in json.items()}

    def token_headers(self):
        basic_auth = base64.b64encode(f"{CLIENT_ID}:".encode('utf-8')).decode('utf-8')
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {basic_auth}',
            'User-Agent': USER_AGENT,
        }

    async def connect(self, username, password):
        self.set_credentials(username, password)
        return (await self.reconnect())

    async def reconnect(self):
        # Get code challenge and verifier
        code_verifier, code_challenge = self.get_code_challenge()
        self.log.debug("Starting Cupra reconnect/auth flow")

        # Get authorize page
        _scope = (
            'openid profile nickname birthdate phone mbb cars address '
            'nationalIdentifier nationality profession badge driversLicense'
        )
        payload = {
            'client_id': CLIENT_ID,
            'scope': _scope,
            'response_type': 'code',
            'nonce': secrets.token_urlsafe(12),
            'redirect_uri': 'cupra://oauth-callback',
            'state': str(uuid.uuid4()),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        response = await self.session.get(LOGIN_BASE + '/authorize', params=payload)
        self.log.debug("Authorize request finished with status=%s", response.status)
        if response.status >= 400:
            self.log.error(f"Authorize: Non-2xx response ({response.status})")
            # Non 2xx response, failed
            return False

        # Fill form with email (username)
        (form, action) = self.form_from_response(await response.read())
        form['email'] = self.username
        self.log.debug("Submitting email form to action=%s", action)
        response = await self.session.post(LOGIN_HANDLER_BASE+action, data=form)
        self.log.debug("Email form response status=%s", response.status)
        if response.status >= 400:
            self.log.error("Email: Non-2xx response")
            return False

        # Fill form with password
        (form, action) = self.password_form(await response.read())
        if not form or not action:
            self.log.error("Password form parsing failed")
            return False
        form['password'] = self.password
        url = LOGIN_HANDLER_BASE + action
        self.log.debug("Submitting password form to url=%s", url)
        response = await self.session.post(url, data=form, allow_redirects=False)
        self.log.debug("Password form response status=%s", response.status)

        # Can get a 303 redirect for a "terms and conditions" page
        if (response.status == 303):
            url = response.headers['Location']
            self.log.debug("Received 303 redirect to %s", url)
            if ("terms-and-conditions" in url):
                # Get terms and conditions page
                url = LOGIN_HANDLER_BASE + url
                self.log.debug("Opening terms and conditions page: %s", url)
                response = await self.session.get(url, data=form, allow_redirects=False)
                (form, action) = self.form_from_response(await response.read())

                url = LOGIN_HANDLER_BASE + action
                self.log.debug("Submitting terms and conditions form to %s", url)
                response = await self.session.post(url, data=form, allow_redirects=False)

                self.log.warning("Agreed to terms and conditions")
            else:
                self.log.error("Got unknown 303 redirect")
                return False

        # Handle every single redirect and stop if the redirect
        # URL uses the seat adapter.
        while (True):
            if 'Location' not in response.headers:
                self.log.error("Redirect handling stopped: missing Location header (status=%s)",
                               response.status)
                return False

            url = response.headers['Location']
            self.log.debug("Redirect: status=%s location=%s", response.status, url)
            if (url.split(':')[0] == "cupra"):
                if not ('code' in url):
                    self.log.error("Missing authorization code")
                    return False
                    # Parse query string
                query_string = url.split('?')[1]
                query = {x[0]: x[1] for x in [x.split("=") for x in query_string.split("&")]}
                self.log.debug("Authorization redirect reached")
                break

            if (response.status != 302):
                self.log.error("Not redirected, status=%u, last_url=%s", response.status, url)
                return False

            response = await self.session.get(url, data=form, allow_redirects=False)

        # Get final token
        form = {}
        form['code'] = query['code']
        form['client_id'] = CLIENT_ID
        form['redirect_uri'] = "cupra://oauth-callback"
        form['grant_type'] = 'authorization_code'
        form['code_verifier'] = code_verifier
        headers = self.token_headers()

        response = await self.session.post(API_BASE + '/authorization/api/v1/token',
                                           headers=headers, data=form)
        self.log.debug("Authorization code exchange status=%s", response.status)
        if response.status >= 400:
            self.log.error("Login: Non-2xx response (%s), body=%s",
                           response.status, await response.text())
            # Non 2xx response, failed
            return False
        self.tokens = self.convert_to_camel_case(await response.json())

        # Update header with final token
        self.headers['Authorization'] = 'Bearer %s' % self.tokens["accessToken"]
        self.log.debug("Cupra authorization completed successfully")

        # Success
        return True

    async def refresh_tokens(self):
        if not self.headers:
            return False

        # Use the refresh token
        form = {}
        form['client_id'] = CLIENT_ID
        form['grant_type'] = 'refresh_token'
        form['refresh_token'] = self.tokens["refreshToken"]
        headers = self.token_headers()

        response = await self.session.post(API_BASE + '/authorization/api/v1/token',
                                           headers=headers, data=form)
        if response.status >= 400:
            self.log.error("Refresh token exchange failed (%s), body=%s",
                           response.status, await response.text())
            return False
        self.tokens = self.convert_to_camel_case(await response.json())

        # Use the newly received access token
        self.headers['Authorization'] = 'Bearer %s' % self.tokens["accessToken"]

        return True

    async def get_status(self):
        self.headers['user-agent'] = USER_AGENT
        self.headers['app-brand'] = 'cupra'
        self.headers['app-market'] = 'android'
        self.headers['app-version'] = '2.16.0'
        status_url = f"{API_BASE}/v1/vehicles/{self.vin}/charging/status"
        statusv2_url = f"{API_BASE}/v2/vehicles/{self.vin}/status"
        mileage_url = f"{API_BASE}/v1/vehicles/{self.vin}/mileage"
        response = await self.session.get(status_url, headers=self.headers)

        # If first attempt fails, try to refresh tokens
        if response.status >= 400:
            self.log.debug("Refreshing tokens")
            if await self.refresh_tokens():
                response = await self.session.get(status_url, headers=self.headers)

        # If refreshing tokens failed, try a full reconnect
        if response.status >= 400:
            self.log.info("Reconnecting")
            if await self.reconnect():
                response = await self.session.get(status_url, headers=self.headers)
            else:
                self.log.error("Reconnect failed")
                return {}

        if response.status >= 400:
            self.log.error("Get status failed")
            return {}

        status_data = await response.json()
        self.log.debug(f"Status data from Cupra API: {status_data}")

        # Fetch mileage data
        response = await self.session.get(mileage_url, headers=self.headers)
        if response.status >= 400:
            self.log.error("Get mileage failed")
            odometer = None
        else:
            mileage_data = await response.json()
            self.log.debug(f"Mileage data from Cupra API: {mileage_data}")
            odometer = mileage_data.get('mileageKm', None)

        # Fetch additional status data from v2 endpoint
        response = await self.session.get(statusv2_url, headers=self.headers)
        if response.status >= 400:
            self.log.error("Get status v2 failed")
        else:
            statusv2_data = await response.json()
            self.log.debug(f"Status v2 data from Cupra API: {statusv2_data}")
            # use current timestamp as a fallback, as the API field is missing
            carCapturedTimestamp = statusv2_data.get(
                'updatedAt',
                datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
            carCapturedTimestamp = carCapturedTimestamp.split('.')[0]
            if not carCapturedTimestamp.endswith('Z'):
                carCapturedTimestamp += 'Z'
            
        battery_value = {
            'currentSOC_pct': status_data['battery']['currentSocPercentage'],
            'cruisingRangeElectric_km': status_data['battery']['estimatedRangeInKm'],
            'carCapturedTimestamp': status_data['battery'].get('updatedAt', carCapturedTimestamp),
            'odometer': odometer,
        }

        return {
            'charging': {
                'batteryStatus': {
                    'value': battery_value,
                }
            }
        }
