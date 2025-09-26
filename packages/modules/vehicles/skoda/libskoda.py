# A Python class to communicate with the "Skoda Connect" API.
# Adapted the libvwid.py module to skoda interface

import secrets
import logging
import json
import uuid
import base64
import hashlib

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    import lxml.html

# Constants
LOGIN_BASE = "https://identity.vwgroup.io/oidc/v1"
LOGIN_HANDLER_BASE = "https://identity.vwgroup.io"
API_BASE = "https://mysmob.api.connect.skoda-auto.cz/api"
CLIENT_ID = "7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com"


class skoda:
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
            self.log.exception("Missing fields in response from Skoda API")
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

    async def connect(self, username, password):
        self.set_credentials(username, password)
        return (await self.reconnect())

    async def reconnect(self):
        # Get code challenge and verifier
        code_verifier, code_challenge = self.get_code_challenge()

        # Get authorize page
        _scope = 'address badge birthdate cars driversLicense dealers email mileage mbb nationalIdentifier'
        _scope = _scope + ' openid phone profession profile vin'
        payload = {
            'client_id': CLIENT_ID,
            'scope': _scope,
            'response_type': 'code id_token',
            'nonce': secrets.token_urlsafe(12),
            'redirect_uri': 'myskoda://redirect/login/',
            'state': str(uuid.uuid4()),
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        response = await self.session.get(LOGIN_BASE + '/authorize', params=payload)
        if response.status >= 400:
            self.log.error(f"Authorize: Non-2xx response ({response.status})")
            # Non 2xx response, failed
            return False

        # Fill form with email (username)
        (form, action) = self.form_from_response(await response.read())
        form['email'] = self.username
        response = await self.session.post(LOGIN_HANDLER_BASE+action, data=form)
        if response.status >= 400:
            self.log.error("Email: Non-2xx response")
            return False

        # Fill form with password
        (form, action) = self.password_form(await response.read())
        form['password'] = self.password
        url = LOGIN_HANDLER_BASE + action
        response = await self.session.post(url, data=form, allow_redirects=False)

        # Can get a 303 redirect for a "terms and conditions" page
        if (response.status == 303):
            url = response.headers['Location']
            if ("terms-and-conditions" in url):
                # Get terms and conditions page
                url = LOGIN_HANDLER_BASE + url
                response = await self.session.get(url, data=form, allow_redirects=False)
                (form, action) = self.form_from_response(await response.read())

                url = LOGIN_HANDLER_BASE + action
                response = await self.session.post(url, data=form, allow_redirects=False)

                self.log.warn("Agreed to terms and conditions")
            else:
                self.log.error("Got unknown 303 redirect")
                return False

        # Handle every single redirect and stop if the redirect
        # URL uses the weconnect adapter.
        while (True):
            url = response.headers['Location']
            if (url.split(':')[0] == "myskoda"):
                if not ('id_token' in url):
                    self.log.error("Missing id token")
                    return False
                    # Parse query string
                query_string = url.split('#')[1]
                query = {x[0]: x[1] for x in [x.split("=") for x in query_string.split("&")]}
                break

            if (response.status != 302):
                self.log.error("Not redirected, status %u" % response.status)
                return False

            response = await self.session.get(url, data=form, allow_redirects=False)

        # Get final token
        params = {
            'tokenType': 'CONNECT'
        }
        payload = {
            'code': query['code'],
            'redirectUri': "myskoda://redirect/login/",
            'verifier': code_verifier
        }
        response = await self.session.post(API_BASE + '/v1/authentication/exchange-authorization-code',
                                           params=params, json=payload)
        if response.status >= 400:
            self.log.error("Login: Non-2xx response")
            # Non 2xx response, failed
            return False
        self.tokens = await response.json()

        # Update header with final token
        self.headers['Authorization'] = 'Bearer %s' % self.tokens["accessToken"]

        # Success
        return True

    async def refresh_tokens(self):
        if not self.headers:
            return False

        params = {
            'tokenType': 'CONNECT'
        }
        # Use the refresh token
        payload = {
            'token': self.tokens["refreshToken"]
        }

        response = await self.session.post(API_BASE + '/v1/authentication/refresh-token', params=params, json=payload)
        if response.status >= 400:
            return False
        self.tokens = await response.json()

        # Use the newly received access token
        self.headers['Authorization'] = 'Bearer %s' % self.tokens["accessToken"]

        return True

    async def get_status(self):
        status_url = f"{API_BASE}/v2/vehicle-status/{self.vin}/driving-range"
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
        self.log.debug(f"Status data from Skoda API: {status_data}")

        return {
            'charging': {
                'batteryStatus': {
                    'value': {
                        'currentSOC_pct': status_data['primaryEngineRange']['currentSoCInPercent'],
                        'cruisingRangeElectric_km': status_data['primaryEngineRange'].get('remainingRangeInKm', 0.0),
                        'carCapturedTimestamp': status_data['carCapturedTimestamp'].split('.')[0] + 'Z',
                    }
                }
            }
        }
