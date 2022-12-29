#!/usr/bin/env python3

import logging
from typing import Union
import asyncio
import json
from modules.common.store import RAMDISK_PATH
from modules.vehicles.smarteq.config import SmartEQ
# import requests
from modules.common import req
import bs4
import pkce
import os
import time
import datetime
import pickle

date_fmt = '%Y-%m-%d %H:%M:%S'
# refreshToken_exp_days = 7    # 7 days before refreshToken expires a new refreshToken shall be stored
initialToken = '1.2.3'

log = logging.getLogger("soc."+__name__)

# Constants
BASE_URL = "https://id.mercedes-benz.com"
OAUTH_URL = BASE_URL + "/as/authorization.oauth2"
LOGIN_URL = BASE_URL + "/ciam/auth/login"
TOKEN_URL = BASE_URL + "/as/token.oauth2"
STATUS_URL = "https://oneapp.microservice.smart.com"
REDIRECT_URI = STATUS_URL
SCOPE = "openid+profile+email+phone+ciam-uid+offline_access"
CLIENT_ID = "70d89501-938c-4bec-82d0-6abb550b0825"
GUID = "280C6B55-F179-4428-88B6-E0CCF5C22A7C"
ACCEPT_LANGUAGE = "de-de"

TOKENS_REFRESH_THRESHOLD = 3600


# helper functions
def nested_key_exists(element: dict, *keys: str) -> bool:
    # Check if *keys (nested) exists in `element` (dict).
    if not isinstance(element, dict):
        raise AttributeError('nested_key_exists() expects dict as first argument - got type ' + str(type(element)))
    if len(keys) == 0:
        raise AttributeError('nested_key_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True


class Api:

    def __init__(self, vehicle: int):
        self.log = logging.getLogger("soc."+__name__)
        self.storeFile = str(RAMDISK_PATH) + '/soc_smarteq_store_vh_' + str(vehicle)
        # LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
        # logging.basicConfig(level=LOGLEVEL)

        # self.method keeps a high level trach of actions
        self.method = ''
        self.soc_ts = 'n/a'
        # self.store is read from ramdisk at start and saved at end.
        # currently is contains:
        # Tokens: refresh- and access-tokens of OAUTH
        # refresh_timestamp: epoch of last refresh_tokens.

        # self.session = requests.session()
        self.session = req.get_http_session()

        self.load_store()
        self.oldTokens = self.store['Tokens']
        self.init = True

    def load_store(self):
        try:
            with open(self.storeFile, "rb") as tf:
                self.store = pickle.load(tf)
                if 'Tokens' not in self.store:
                    self.store['Tokens'] = {}
                    self.store['refresh_timestamp'] = int(0)
        except Exception:
            log.exception("init: loading stored data failed, file: " + self.storeFile)
            self.store = {}
            self.store['Tokens'] = {}
            self.store['refresh_timestamp'] = int(0)

    def write_store(self):
        try:
            tf = open(self.storeFile, "wb")
        except Exception:
            log.exception("write_store")
            os.system("sudo rm -f " + self.storeFile)
            tf = open(self.storeFile, "wb")
        pickle.dump(self.store, tf)
        tf.close()
        try:
            os.chmod(self.storeFile, 0o777)
        except Exception:
            log.exception("chmod_store")
            os.system("sudo chmod 0777 " + self.storeFile)

    # ===== get resume string ======
    def get_resume(self) -> str:
        response_type = "code"
        self.code_verifier, self.code_challenge = pkce.generate_pkce_pair()
        self.code_challenge_method = "S256"
        url = OAUTH_URL + '?client_id=' + CLIENT_ID + '&response_type=' + response_type + '&scope=' + SCOPE
        url = url + '&redirect_uri=' + REDIRECT_URI
        url = url + '&code_challenge=' + self.code_challenge + '&code_challenge_method=' + self.code_challenge_method
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": ACCEPT_LANGUAGE,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_1 like Mac OS X)\
            AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        }

        try:
            response = self.session.get(url, headers=headers)

            soup = bs4.BeautifulSoup(response.text, 'html.parser')

            for cd in soup.findAll(text=True):
                if "CDATA" in cd:
                    self.log.debug("get_resume: cd.CData= " + str(cd))
                    for w in cd.split(','):
                        if w.find("const initialState = ") != -1:
                            iS = w
            if iS:
                js = iS.split('{')[1].split('}')[0].replace('\\', '').replace('\\"', '"').replace('""', '"')
                self.resume = js[1:len(js)-1].split(':')[1][2:]
            self.log.debug("get_resume: resume = " + self.resume)
        except Exception:
            log.exception('get_resume')
        return self.resume

    # login to website, return (intermediate) token
    def login(self) -> str:
        url = LOGIN_URL + "/pass"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_1 like Mac OS X)\
            AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": LOGIN_URL,
            "Accept-Language": ACCEPT_LANGUAGE
        }
        data = json.dumps({'username': self.username,
                           'password': self.password,
                           'rememberMe': 'true'})

        try:
            response = self.session.post(url, headers=headers, data=data)
            self.log.debug("login: status_code = " + str(response.status_code))
            if response.status_code >= 400:
                self.log.error("login: failed, status_code = " + str(response.status_code) +
                               ", check username/password")
                token = ""
            else:
                result_json = json.loads(str(bs4.BeautifulSoup(response.text, 'html.parser')))
                self.log.debug("login: result_json:\n" + json.dumps(result_json))
                token = result_json['token']
                self.log.debug("login: token = " + token)
        except Exception:
            self.log.eexception('login')
            token = ""
        return token

    # get code
    def get_code(self) -> str:
        url = BASE_URL + '/' + self.resume
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_1 like Mac OS X)\
            AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": LOGIN_URL,
            "Accept-Language": ACCEPT_LANGUAGE,
        }
        data = json.dumps({'token': self.token})

        try:
            response = self.session.post(url, headers=headers, data=data)
            code = response.url.split('?')[1].split('=')[1]
            self.log.debug("get_code: code=" + code)
        except Exception:
            log.exception("get_code")
        return code

    # get Tokens
    def get_tokens(self) -> dict:
        self.method += " 3-full (re)connect"
        self.resume = self.get_resume()
        self.token = self.login()
        if self.token == "":
            self.log.error("login: Login failed - check username/password")
            return ""
        code = self.get_code()
        if code == "":
            self.log.warn("get_tokens: get_code failed")
            return {}
        url = TOKEN_URL
        headers = {
            "Accept": "*/*",
            "User-Agent": "sOAF/202108260942 CFNetwork/978.0.7 Darwin/18.7.0",
            "Accept-Language": ACCEPT_LANGUAGE,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "grant_type=authorization_code&code=" + code + "&code_verifier=" + self.code_verifier +\
               "&redirect_uri=" + REDIRECT_URI + "&client_id=" + CLIENT_ID

        try:
            response = self.session.post(url, headers=headers, data=data)

            Tokens = json.loads(response.text)
            if not Tokens['access_token']:
                self.log.warn("get_tokens: no access_token found")
                Tokens = {}
            else:
                self.log.debug("Tokens=\n" + json.dumps(Tokens, indent=4))
        except Exception:
            log.exception('get_tokens')
        return Tokens

    # refresh tokens
    def refresh_tokens(self) -> dict:
        self.method += " 2-refresh_tokens"
        url = TOKEN_URL
        newTokens = {}
        headers = {
            "Accept": "*/*",
            "User-Agent": "sOAF/202108260942 CFNetwork/978.0.7 Darwin/18.7.0",
            "Accept-Language": ACCEPT_LANGUAGE,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "grant_type=refresh_token&client_id=" + CLIENT_ID + "&refresh_token=" +\
               self.store['Tokens']['refresh_token']

        try:
            response = self.session.post(url,
                                         headers=headers,
                                         data=data,
                                         verify=True,
                                         allow_redirects=False,
                                         timeout=(30, 30))

            newTokens = json.loads(response.text)
            if 'error' in newTokens and newTokens['error'] == 'unauthorized':
                self.log.warning("refresh_tokens: error: " + newTokens['error'] + ', ' + newTokens['error_description'])
            if 'access_token' not in newTokens:
                self.log.debug("refresh_tokens: new access_token not found")
                newTokens['access_token'] = ""
            if 'refresh_token' not in newTokens:
                self.log.debug("refresh_tokens: new refresh_token not found")
                newTokens['refresh_token'] = ""
            self.log.debug("refresh_tokens: newTokens=\n" + json.dumps(newTokens, indent=4))
        except Exception:
            log.exception('refresh_tokens')
            newTokens['access_token'] = ""
            newTokens['refresh_token'] = ""
        return newTokens

    # reconnect to Server
    def reconnect(self) -> dict:
        # check if we have a refresh token and last refresh was more then 1h ago (3600s)
        if 'refresh_token' in self.store['Tokens']:
            now = int(time.time())
            secs_since_refresh = now - self.store['refresh_timestamp']
            if secs_since_refresh > TOKENS_REFRESH_THRESHOLD:
                # try to refresh tokens
                new_tokens = self.refresh_tokens()
                self.store['refresh_timestamp'] = int(time.time())
                _ref = True
            else:
                # keep existing tokens
                return self.store['Tokens']
        else:
            self.log.debug("reconnect: refresh_token not found in self.store['Tokens']=" +
                           json.dumps(self.store['Tokens'], indent=4))
            new_tokens = {'refresh_token': '', 'access_token': ''}
            _ref = False
        self.log.debug("reconnect: new_tokens=" + json.dumps(new_tokens, indent=4))
        if new_tokens['access_token'] == '':
            if _ref:
                self.log.warning("reconnect: refresh access_token failed, try full reconnect")
            Tokens = self.get_tokens()
        else:
            self.log.debug("reconnect: refresh access_token successful")
            Tokens = self.store['Tokens']   # replace expired access and refresh token by new tokens
            for key in new_tokens:
                Tokens[key] = new_tokens[key]
                self.log.debug("reconnect: replace Tokens[" + key + "], new value: " + str(Tokens[key]))

        return Tokens

    # get Soc,range of Vehicle
    def get_status(self, vin: str) -> int:
        self.method += " 1-get_status"
        if self.init:
            url = STATUS_URL + "/seqc/v0/vehicles/" + vin +\
                   "/init-data?requestedData=BOTH&countryCode=DE&locale=de-DE"
        else:
            url = STATUS_URL + "/seqc/v0/vehicles/" + vin + "/refresh-data"
            self.init = False

        headers = {
            "accept": "*/*",
            "accept-language": "de-DE;q=1.0",
            "authorization": "Bearer " + self.store['Tokens']['access_token'],
            "x-applicationname": CLIENT_ID,
            "user-agent": "Device: iPhone 6; OS-version: iOS_12.5.1; App-Name: smart EQ control; App-Version: 3.0;\
            Build: 202108260942; Language: de_DE",
            "guid": GUID
        }

        try:
            response = self.session.get(url, headers=headers)
            res = json.loads(response.text)
            res_json = json.dumps(res, indent=4)
            if (nested_key_exists(res, 'precond', 'data', 'soc', 'value') and
               nested_key_exists(res, 'precond', 'data', 'rangeelectric', 'value')):
                _ts = res['precond']['data']['soc']['ts']
                self.soc_ts = datetime.datetime.fromtimestamp(_ts).strftime('%Y-%m-%d %H:%M:%S')
                _ts = res['precond']['data']['rangeelectric']['ts']
                rng_ts = datetime.datetime.fromtimestamp(_ts).strftime('%Y-%m-%d %H:%M:%S')
                res_json = "{\nsoc: " + json.dumps(res['precond']['data']['soc'], indent=4).replace("\n", "\n    ")
                res_json += ",\nsoc.timestamp: \"" + self.soc_ts + "\""
                res_json += ",\nrangeelectric: " +\
                            json.dumps(res['precond']['data']['rangeelectric'], indent=4).replace("\n", "\n    ")
                res_json += ",\nrange.timestamp: \"" + rng_ts + "\"\n}"
                if rng_ts > self.soc_ts:
                    self.soc_ts = rng_ts
                try:
                    soc = int(res['precond']['data']['soc']['value'])
                    range = float(res['precond']['data']['rangeelectric']['value'])
                    self.log.debug("get_status: result json:\n" + res_json)
                except Exception:
                    soc = -1
                    range = 0.0
            elif 'error' in res and res['error'] == 'unauthorized':
                self.log.warning("get_status: access_token expired - try refresh")
                self.log.debug("get_status: error - result json:\n" + res_json)
                soc = -1
                range = 0.0

        except Exception:
            log.exception('get_status')
            self.log.debug("get_status: result:\n" + res_json)
            soc = -1
            range = 0.0
        if "Vehicle not found" in res_json:
            soc = -2
            range = 0.0
        return soc, range

    # fetch soc in 3 stages:
    #   1. get_status via stored access_token
    #   2. if expired: refresh_access_token using id and refresh token, then get_status
    #   3. if refresh token expired: login, get tokens, then get_status
    async def _fetch_soc(self,
                         conf: SmartEQ,
                         vehicle: int) -> Union[int, float]:
        self.username = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.vehicle = vehicle

        try:
            soc = -1
            range = 0.0
            if 'refresh_token' in self.store['Tokens']:
                self.store['Tokens'] = self.reconnect()
            if 'access_token' in self.store['Tokens']:
                soc, range = self.get_status(self.vin)
                if soc > 0:
                    self.log.debug("fetch_soc: 1st attempt successful")
                else:
                    self.log.debug("fetch_soc: 1st attempt failed - soc=" + str(soc))

            if soc == -1:
                self.log.debug("fetch_soc: (re)connecting ...")
                self.store['Tokens'] = self.reconnect()
                if 'access_token' in self.store['Tokens']:
                    soc, range = self.get_status(self.vin)
                    if soc > 0:
                        self.log.debug("fetch_soc: 2nd attempt successful")
                    else:
                        self.log.warning("fetch_soc: 2nd attempt failed - soc=" + str(soc))
                        range = 0.0
                else:
                    self.log.error("fetch_soc: (re-)connect failed")
                    soc = 0
                    range = 0.0
            elif soc == -2:
                self.log.error("get_status failed, verify VIN ...")
                soc = 0
                range = 0.0

        except Exception:
            log.exception("fetch_soc: exception, (re-)connecting ...")
            self.store['Tokens'] = self.reconnect()
            if 'access_token' in self.store['Tokens']:
                soc, range = self.get_status(self.vin)
        self.log.info(" SOC/Range: " + str(soc) + '%/' + str(range) +
                      '@' + self.soc_ts +
                      ', Method: ' + self.method)

        if self.store['Tokens'] != self.oldTokens:
            self.log.debug("reconnect: tokens changed, store token file")
            self.write_store()

        return soc, range


def fetch_soc(conf: SmartEQ, vehicle: int) -> Union[int, float]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = Api(vehicle)
    soc, range = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range
