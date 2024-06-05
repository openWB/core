#!/usr/bin/env python3

import logging
from typing import Optional

from modules.common import req
from typing import NamedTuple
from modules.common.component_state import CarState
import requests
import json
import hashlib
import hmac
import base64
import random
import string
import time
import urllib.parse
from typing import Tuple

from modules.vehicles.smarthello.config import SmartHelloConfiguration

log = logging.getLogger(__name__)
'''
def create_session(user_id: str, password: str, client_id: Optional[str], client_secret: Optional[str],
                   manufacturer: str) -> req.Session:
    manufacturer_config = manufacturer_configurations[manufacturer]
    brand = manufacturer_config.brand
    realm = manufacturer_config.realm
    if not client_id or not client_secret:  # use defaults if no client_id and client_secret is specified
        client_id = manufacturer_config.client_id
        client_secret = manufacturer_config.client_secret
        if not client_id or not client_secret:
            raise Exception(
                "No OAuth credentials configured and no default available for manufacturer %s" % manufacturer)

    session = req.get_http_session()
    data = {
        'realm': realm, 'grant_type': 'password', 'password': password, 'username': user_id, 'scope': 'openid profile'
    }

    access_token = session.post(
        "https://idpcvs." + str(brand) + "/am/oauth2/access_token", data=data, auth=(client_id, client_secret)
    ).json()['access_token']

    session.params = {"client_id": client_id}
    session.headers = {
        'Accept': 'application/hal+json', 'Authorization': 'Bearer %s' % access_token, 'x-introspect-realm': realm
    }
    return session
'''

def fetch_vehicle(vin: str, session: req.Session) -> dict:

    vehicle_response = session.get(
        "https://api.groupe-psa.com/connectedcar/v4/user/vehicles").json()
    vehicles = vehicle_response['_embedded']['vehicles']

    # Filter list for given VIN or select first entry if no VIN is provided
    try:
        vehicle_selected = next(
            vehicle for vehicle in vehicles if vehicle['vin'] == vin) if vin else vehicles[0]
    except StopIteration:
        raise Exception("Cannot find VIN: '" + str(vin) + "'")

    return vehicle_selected


def fetch_energy(vin_id: str, session: req.Session) -> dict:
    battery = session.get(
        "https://api.groupe-psa.com/connectedcar/v4/user/vehicles/" + str(vin_id) + "/status").json()

    # filter to only include type=Electric but remove all others. Seen type=Fuel and type=Electric being returned.
    energies = battery['energy']
    energy_selected = next(energy for energy in energies if energy['type'] == 'Electric')
    return energy_selected


def create_session():
    # add session restore functionality, include cookies jar and access tokens

    
    session = req.Session()
    session.headers.update({'user-agent': 'Mozilla/5.0 (Linux; Android 9; ANE-LX1 Build/HUAWEIANE-L21; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36'})
    session.headers.update({'x-requested-with': 'com.smart.hellosmart'})
    session.headers.update({'accept-language': 'de-DE,de;q=0.9,en-DE;q=0.8,en-US;q=0.7,en;q=0.6'})
    #session.cookies = requests.cookies.RequestsCookieJar()
    return session


def onReady(self):
    return


def loginHello(session: req.Session, config: SmartHelloConfiguration) -> dict :
    log.debug('Login into Hello Smart')
    response = session.get(
        'https://awsapi.future.smart.com/login-app/api/v1/authorize?uiLocales=de-DE&uiLocales=de-DE',
        headers={
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document'
        }
    )
    parsed_url = urllib.parse.urlparse(response.url)  # Parse the URL
    query_params = urllib.parse.parse_qs(parsed_url.query)  # Parse the query parameters
    context = query_params.get('context', [''])[0]  # Get the 'context' parameter

    loginResponse = session.post(
        'https://auth.smart.com/accounts.login',
        headers={
            'content-type': 'application/x-www-form-urlencoded',
            'accept': '*/*',
            'origin': 'https://app.id.smart.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'cookie': 'gmid=gmid.ver4.AcbHPqUK5Q.xOaWPhRTb7gy-6-GUW6cxQVf_t7LhbmeabBNXqqqsT6dpLJLOWCGWZM07EkmfM4j.u2AMsCQ9ZsKc6ugOIoVwCgryB2KJNCnbBrlY6pq0W2Ww7sxSkUa9_WTPBIwAufhCQYkb7gA2eUbb6EIZjrl5mQ.sc3; ucid=hPzasmkDyTeHN0DinLRGvw; hasGmid=ver4; gig_bootstrap_3_L94eyQ-wvJhWm7Afp1oBhfTGXZArUfSHHW9p9Pncg513hZELXsxCfMWHrF8f5P5a=auth_ver4',
        },
        data={
            'loginID': config.user_id,
            'password': config.password,
            'sessionExpiration': '2592000',
            'targetEnv': 'jssdk',
            'include': 'profile,data,emails,subscriptions,preferences,',
            'includeUserInfo': 'true',
            'loginMode': 'standard',
            'lang': 'de',
            'riskContext': '{"b0":41187,"b1":[0,2,3,1],"b2":4,"b3":["-23|0.383","-81.33333587646484|0.236"],"b4":3,"b5":1,"b6":"Mozilla/5.0 (Linux; Android 9; ANE-LX1 Build/HUAWEIANE-L21; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/118.0.0.0 Mobile Safari/537.36","b7":[],"b8":"16:33:26","b9":-60,"b10":null,"b11":false,"b12":{"charging":true,"chargingTime":null,"dischargingTime":null,"level":0.58},"b13":[5,"360|760|24",false,true]}',
            'APIKey': '3_L94eyQ-wvJhWm7Afp1oBhfTGXZArUfSHHW9p9Pncg513hZELXsxCfMWHrF8f5P5a',
            'source': 'showScreenSet',
            'sdk': 'js_latest',
            'authMode': 'cookie',
            'pageURL': 'https://app.id.smart.com/login?gig_ui_locales=de-DE',
            'sdkBuild': '15482',
            'format': 'json',
        }
    ).json()

    if not loginResponse:
        log.debug('Login failed #1')
        raise Exception('Login failed #1')

    if not loginResponse.get('sessionInfo'):
        log.error('Login failed no session found:')
        log.error(json.dumps(loginResponse))
        raise Exception("Login failed no session found")

    TokenResponse = session.get(
        'https://auth.smart.com/oidc/op/v1.0/3_L94eyQ-wvJhWm7Afp1oBhfTGXZArUfSHHW9p9Pncg513hZELXsxCfMWHrF8f5P5a/authorize/continue',
        params={'context': context, 'login_token': loginResponse['sessionInfo']['login_token']},
        headers={
            'upgrade-insecure-requests': '1',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'cookie': 'gmid=gmid.ver4.AcbHPqUK5Q.xOaWPhRTb7gy-6-GUW6cxQVf_t7LhbmeabBNXqqqsT6dpLJLOWCGWZM07EkmfM4j.u2AMsCQ9ZsKc6ugOIoVwCgryB2KJNCnbBrlY6pq0W2Ww7sxSkUa9_WTPBIwAufhCQYkb7gA2eUbb6EIZjrl5mQ.sc3; ucid=hPzasmkDyTeHN0DinLRGvw; hasGmid=ver4; gig_bootstrap_3_L94eyQ-wvJhWm7Afp1oBhfTGXZArUfSHHW9p9Pncg513hZELXsxCfMWHrF8f5P5a=auth_ver4; glt_3_L94eyQ-wvJhWm7Afp1oBhfTGXZArUfSHHW9p9Pncg513hZELXsxCfMWHrF8f5P5a=' + loginResponse['sessionInfo']['login_token'],
        },
        allow_redirects=True)

    parsed_url = urllib.parse.urlparse(TokenResponse.url)  # Parse the URL
    loginToken = urllib.parse.parse_qs(parsed_url.query)  # Parse the query parameters
    
    log.debug('Login successful')
    return loginToken


def create_signature(method: str, path: str, params: dict, body: Optional[str]) -> Tuple[str, str, str, None]:
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    ts = str(int(time.time() * 1000))

    md5_hash = "1B2M2Y8AsgTpgAmY7PhCfg=="
    if body:
        md5 = hashlib.md5()
        md5.update(body.encode())
        md5_hash = base64.b64encode(md5.digest()).decode()

    payload = f"""application/json;responseformat=3
x-api-signature-nonce:{nonce}
x-api-signature-version:1.0

{urllib.parse.urlencode(params)}
{md5_hash}
{ts}
{method}
{path}"""

    secret = base64.b64decode("NzRlNzQ2OWFmZjUwNDJiYmJlZDdiYmIxYjM2YzE1ZTk=")

    hmac_obj = hmac.new(secret, payload.encode(), hashlib.sha1)
    sign = base64.b64encode(hmac_obj.digest()).decode()

    return nonce, ts, sign, None


def getCurrentToken(session, Tokens: dict, deviceId) -> dict:
    params = {'identity_type': 'smart'}
    method = 'POST'
    url = '/auth/account/session/secure'
    data = {
        'accessToken': Tokens['access_token'][0]
    }

    nonce, timestamp, sign, err = create_signature(method, url, params, json.dumps(data))
    response = session.post(
        'https://api.ecloudeu.com/auth/account/session/secure',
        headers={
            'x-app-id': 'SmartAPPEU',
            'accept': 'application/json;responseformat=3',
            'x-agent-type': 'android',
            'x-device-type': 'mobile',
            'x-operator-code': 'SMART',
            'x-device-identifier': deviceId,
            'x-env-type': 'production',
            'x-version': 'smartNew',
            'accept-language': 'en_US',
            'x-api-signature-version': '1.0',
            'x-api-signature-nonce': nonce,
            'x-device-manufacture': 'HUAWEI',
            'x-device-brand': 'ANE-LX1',
            'x-device-model': 'ANE-LX1',
            'x-device-release-date': '',
            'x-agent-version': '9',
            'content-type': 'application/json; charset=utf-8',
            'user-agent': 'okhttp/4.11.0',
            'x-signature': sign,
            'x-timestamp': timestamp,
        },
        json=data,
        params=params
    ).json()
    # add error handling if result is unexepcted or does not contain tokens
    return response['data']


def getDeviceListHello(session, tokens: dict, deviceId) -> list:
    deviceArray = []

    params = {'needSharedCar': 1, 'userId': tokens['userId']}
    method = 'GET'
    url = '/device-platform/user/vehicle/secure'

    nonce, timestamp, sign, err = create_signature(method, url, params, '')
    response =session.get(
        'https://api.ecloudeu.com' + url,
        headers={
            'x-app-id': 'SmartAPPEU',
            'accept': 'application/json;responseformat=3',
            'x-agent-type': 'android',
            'x-device-type': 'mobile',
            'x-operator-code': 'SMART',
            'x-device-identifier': deviceId,
            'x-env-type': 'production',
            'x-version': 'smartNew',
            'accept-language': 'en_US',
            'content-type': 'application/json; charset=utf-8',
            'x-api-signature-version': '1.0',
            'x-api-signature-nonce': nonce,
            'authorization': tokens['accessToken'],
            'x-client-id': 'UAWEI0000APP00ANELX123AV10090080',
            'user-agent': 'okhttp/4.11.0',
            'x-signature': sign,
            'x-timestamp': timestamp,
        },
        params=params
    ).json()

    if not response or not response.get('data') or response['data'].get('list') == 0:
        log.info('No vehicles found')
        log.debug(response)
        return

    log.debug('Found ' + str(len(response['data']['list'])) + ' vehicles')
    log.debug(response['data']['list'])
    for device in response['data']['list']:
        vin = device['vin']
        log.debug('Found vehicle with VIN ' + vin)
        deviceArray.append(vin)
    
    return deviceArray


def updateDevicesHello(session, tokens, deviceId, vin) -> dict:

        
    log.debug("Updating vehicle status for " + vin + " ...")
    params = {'latest': True, 'target': '', 'userId': tokens['userId']}
    method = 'GET'
    url = '/remote-control/vehicle/status/' + vin

    nonce, timestamp, sign, err = create_signature(method, url, params, '')
    response = session.get(
        'https://api.ecloudeu.com' + url,
        headers={
            'x-app-id': 'SmartAPPEU',
            'accept': 'application/json;responseformat=3',
            'x-agent-type': 'android',
            'x-device-type': 'mobile',
            'x-operator-code': 'SMART',
            'x-device-identifier': deviceId,
            'x-env-type': 'production',
            'x-version': 'smartNew',
            'accept-language': 'en_US',
            'content-type': 'application/json; charset=utf-8',
            'x-api-signature-version': '1.0',
            'x-api-signature-nonce': nonce,
            'authorization': tokens['accessToken'],
            'x-client-id': 'UAWEI0000APP00ANELX123AV10090080',
            'user-agent': 'okhttp/4.11.0',
            'x-signature': sign,
            'x-timestamp': timestamp,
        },
        params=params
    ).json()

    #if response['code'] == '1402':
    #    getCurrentToken(session, tokens, deviceId)
    #    continue

    #if not response or not response.get('data') or not response['data'].get('vehicleStatus'):
    #    continue
    
    return response['data']['vehicleStatus']


#def setState(self, state, value):
#    # Add the setState functionality
#    pass

def getState(self, state):
    # Add the getState functionality
    pass


def random_hex(n):
    return ''.join(random.choice(string.hexdigits) for _ in range(n))


#def log(self, message):
#    print(message)




def fetch_soc(config: SmartHelloConfiguration,
              vehicle_id: int) -> CarState:

    try:
        session = create_session()
        deviceId = random_hex(16)

        LoginToken = loginHello(session, config)
        tokens = getCurrentToken(session, LoginToken, deviceId)

        if tokens.get('accessToken'):
            log.debug('Login successful, retrieving vehicle list')
            vehicles = getDeviceListHello(tokens)
            # check if configured VIN is empty or is in list
            if not config.vin or config.vin in vehicles:    
                log.debug('Retrieving vehicle status')
                data = updateDevicesHello(session, tokens, deviceId, config.vin)
            else:
                raise Exception(f"VIN {config.vin} not found in vehicle list {vehicles}")

            log.debug(data["additionalVehicleStatus"]["electricVehicleStatus"]["chargeLevel"])
            log.debug(data["additionalVehicleStatus"]["electricVehicleStatus"]["distanceToEmptyOnBatteryOnly"])
            log.debug(data["additionalVehicleStatus"]["electricVehicleStatus"])
            log.debug('Vehicle status updated')


            vehicle = fetch_vehicle(config.vin, session)
            log.debug("Fetching details for VIN: %s with vehicle_id: %s", vehicle['vin'], vehicle['id'])
            energy = fetch_energy(vehicle['id'], session)

    except Exception:
        raise Exception("Error requesting for vehicle: %s" % vehicle_id)
    
    soc=data["additionalVehicleStatus"]["electricVehicleStatus"]["chargeLevel"]
    range=data["additionalVehicleStatus"]["electricVehicleStatus"]["distanceToEmptyOnBatteryOnly"]

    log.info("Smart Hello Data: soc=%s%%, range=%s, timestamp=%s",
             soc, range, None)
    return CarState(soc=soc, range=range, soc_timestamp=None)
