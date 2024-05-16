#!/usr/bin/env python3

import logging
from typing import Union
import asyncio
import json
import bs4
import pkce
import os
import time
import datetime
import copy
import urllib
import uuid
import requests
from modules.common.component_state import CarState
from modules.common.store import RAMDISK_PATH
from modules.vehicles.smarteq.config import SmartEQ
from modules.common import req
from modules.vehicles.smarteq.socutils import socUtils
import websocket
import modules.vehicles.smarteq.proto.vehicle_events_pb2 as vehicle_events_pb2
from google.protobuf.json_format import MessageToJson
import threading

date_fmt = '%Y-%m-%d %H:%M:%S'
initialToken = '1.2.3'

# Constants
BASE_URL = "https://id.mercedes-benz.com"
OAUTH_URL = BASE_URL + "/as/authorization.oauth2"
LOGIN_URL = BASE_URL + "/ciam/auth/login"
TOKEN_URL = BASE_URL + "/as/token.oauth2"
STATUS_URL_SMART = "https://oneapp.microservice.smart.mercedes-benz.com"
STATUS_URL_MERCEDES = "https://bff.emea-prod.mobilesdk.mercedes-benz.com"
STATUS_URL = STATUS_URL_SMART
REDIRECT_URI = STATUS_URL
SCOPE = "openid+profile+email+phone+ciam-uid+offline_access"
CLIENT_ID = "70d89501-938c-4bec-82d0-6abb550b0825"
GUID = "280C6B55-F179-4428-88B6-E0CCF5C22A7C"
ACCEPT_LANGUAGE = "de-DE;q=1.0"
TOKENS_REFRESH_THRESHOLD = 3600
TOKENS_REFRESH_THRESHOLD_WS = 604800  # 1 week
SSL_VERIFY_AUTH = True
SSL_VERIFY_STATUS = True

# Constants 2FA
LOGIN_APP_ID = "01398c1c-dc45-4b42-882b-9f5ba9f175f1"
COUNTRY_CODE = "DE"
X_APPLICATIONNAME_ECE = "mycar-store-ece"
RIS_APPLICATION_VERSION = "1.40.0 (2097)"
RIS_OS_NAME = "ios"
RIS_OS_VERSION = "17.3"
RIS_SDK_VERSION = "2.111.1"
X_LOCALE = "de-DE"
WEBSOCKET_USER_AGENT = "MyCar/1.40.0 (com.daimler.ris.mercedesme.ece.ios; build:2097; iOS 17.3.0) Alamofire/5.4.0"
STATUS_USER_AGENT = "Device: iPhone 6; OS-version: iOS_12.5.1; App-Name: smart EQ control; App-Version: 3.0;\
                    Build: 202108260942; Language: de_DE"
CONTENT_TYPE_OAUTH = "application/x-www-form-urlencoded"
CONTENT_TYPE = "application/json"
ACCEPT = "*/*"
WEBSOCKET_API_BASE = "wss://websocket.emea-prod.mobilesdk.mercedes-benz.com/ws"
WS_THREAD_NAME = 'soc_smarteq_ws'
USER_AGENT_OAUTH = 'sOAF/202108260942 CFNetwork/978.0.7 Darwin/18.7.0'


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

    def __init__(self, conf: SmartEQ, vehicle: int):
        self.log = logging.getLogger(__name__)

        self.conf = conf
        self.username = conf.configuration.user_id
        self.password = conf.configuration.password
        if self.password is None:
            self.password = ""
        self.pin = conf.configuration.pin
        self.vin = conf.configuration.vin

        if type(conf.configuration.useWebSocket) == bool:
            self.useWebSocket = conf.configuration.useWebSocket
        elif type(conf.configuration.useWebSocket) == str:
            self.useWebSocket = json.loads(conf.configuration.useWebSocket)
        else:
            # if not properly defined set to False
            self.useWebSocket = False

        self.refreshToken = conf.configuration.refreshToken
        self.refreshTokenMQTT = self.refreshToken

        self.last_opmode = conf.configuration.opMode
        if self.last_opmode is None:
            self.last_opmode = 'unknown'
        self.vehicle = vehicle
        # configurable logging Filter, will come from configuration
        self.logFilter = conf.configuration.logFilter
        if self.logFilter is None:
            self.logFilter = ''
        self.write_store_count = 0

        self.su = socUtils()

        self.storeFile = str(RAMDISK_PATH) + '/soc_smarteq_store_vh_' + str(vehicle)
        self.ws_storeFile = str(RAMDISK_PATH) + '/soc_smarteq_store_ws'
        self.messageFile = str(RAMDISK_PATH) + '/soc_smarteq_message_vh_' + str(vehicle)

        if self.useWebSocket is True:
            self.vhList = self.su.get_vin_ev_map()
            self._infoLog('i', "vehicle_vin_num_mapping=\n" + json.dumps(self.vhList, indent=4))
            tn = self.ws_fname(self.vin)
            if os.path.exists(tn):
                self.load_ws_store(self.vin)
            else:
                self.init_ws_store(self.vin)
                self.write_ws_store(self.vin)

        # LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
        # logging.basicConfig(level=LOGLEVEL)

        # self.method keeps a high level trace of actions
        self.method = ''
        self.soc_ts = 'n/a'
        # self.store is read from ramdisk at start and saved at end.

        self.session = req.get_http_session()

        self._infoLog('i', "init: pre init_store, refreshToken=" + self.refreshToken)
        self.init_store(False)
        self._infoLog('i', "init: pre load_store, refreshToken=" + self.refreshToken)
        self._infoLog('i', "init: pre load_store, store-refreshToken=" + self.store['Tokens']['refresh_token'])
        self.opmode = self.last_opmode
        self.load_store()
        self._infoLog('i', "init: post load_store, refreshToken=" + self.refreshToken)
        self._infoLog('i', "init: post load_store, store-refreshToken=" + self.store['Tokens']['refresh_token'])
        self.store['Tokens']['refresh_token'] = self.refreshToken
        self.store['logFilter'] = self.logFilter

        self._infoLog('i', 'last_opmode from conf: ' + self.last_opmode)
        # if 'opmode' in self.store:
        #     self.last_opmode = self.store['opmode']
        #     self._infoLog('i', 'last_opmode from store: ' + self.last_opmode)

        if self.password is not None and self.password != '':
            self.opmode = 'pw-rest'
        elif self.useWebSocket is False:
            self.opmode = 'pin-rest'
        else:
            self.opmode = 'pin-ws'
        self._infoLog('i', 'current opmode: ' + self.opmode)

        if 'pin' in self.opmode and 'pin' in self.last_opmode:
            self._infoLog('i', 'lst and current opmode are pin-based, last:' + self.last_opmode +
                          ', current:' + self.opmode)
        else:
            self._infoLog('i', 'switch opmode from ' + self.last_opmode + ' to ' + self.opmode)
            self.store['opmode'] = self.opmode
            # forget old token
            self._infoLog('i', 'forget old tokens to force new authentication')
            self.refreshToken = initialToken
            self.refreshTokenMQTT = initialToken
            self.store['Tokens']['refresh_token'] = initialToken
            self.store['Tokens']['access_token'] = initialToken
            self.authState = 'init'

        if self.refreshToken is not None and self.refreshToken != '':
            self._infoLog('i', 'use refreshToken from config: ' + self.refreshToken)
            self.store['Tokens']['refresh_token'] = self.refreshToken
            self.refreshTokenMQTT = self.refreshToken
        elif 'refresh_token' in self.store['Tokens']:
            self._infoLog('i', 'use refreshToken from store: ' + self.store['Tokens']['refresh_token'])
            self.refreshTokenMQTT = self.store['Tokens']['refresh_token']
            self.refreshToken = self.store['Tokens']['refresh_token']
        else:
            self._infoLog('i', 'reset refreshToken to initialToken')
            self.refreshToken = initialToken
            self.refreshTokenMQTT = self.refreshToken

        if self.password != "" and self.password is not None and self.useWebSocket is True:
            self.log.warning("smartEQ: in password auth mode WebSockets cant be used - set disable WebSocket")
            self.useWebSocket = False

        self._infoLog('i', 'init, write store refreshToken: ' + self.store['Tokens']['refresh_token'])
        self.write_store()
        self.oldTokens = copy.deepcopy(self.store['Tokens'])

        self._country_code = COUNTRY_CODE

        # init thread for web socket interface if configured and not running yet
        if self.useWebSocket is True:
            self.ws_thread_name = WS_THREAD_NAME
            self.su.set_threadname = self.ws_thread_name.replace('_ws', '_mqtt')
            self.su.set_logFilter = self.logFilter
            self.ws_thread = None
            for t in threading.enumerate():
                if t.name == self.ws_thread_name:
                    self._infoLog('i', self.ws_thread_name + ' found: name = ' + t.name)
                    self.ws_thread = t
            if self.ws_thread is None:
                self._infoLog('i', self.ws_thread_name + ' not found: starting now')
                self.ws_thread = threading.Thread(target=self.wsThread, name=self.ws_thread_name)
                self.ws_thread.start()
        else:
            self._infoLog('i', "useWebSocket not configured")

    # configurable filtered logging
    # log as info if filter is in configured filter string
    # A: ALL
    # f: fetch_soc
    # i: initialization
    # m: websocket message
    # M: websocket message details
    # q: mqtt logging
    # Q: mqtt logging details
    # r: smart eq rest api
    # s: state changes
    # t: token refresh
    # T: token refresh details
    # u: authentication
    # U: authentication details
    # w: webSocket interface
    # W: webSocket interface details
    # X: simulate range changes
    def _infoLog(self, filter: str, txt: str):
        if filter in self.logFilter or 'A' in self.logFilter:
            self.log.info('(' + filter + '): ' + txt)

    # set_authState
    # authState: 'init'
    #            'authenticated'
    #            'tokenRequested'
    #            'pinRequested'
    #            'accessTokenExpired'
    def set_authState(self, state: str):
        if 'authState' in self.store:
            old_state = self.store['authState']
        else:
            old_state = 'n/a'
        self.store['authState'] = state
        self._infoLog('s', 'set_authState from ' + old_state + ' to ' + state)
        self.write_store()

    # initialize store structures when no store is available
    def init_store(self, write: bool):
        self.store = {}
        self.store['Tokens'] = {}
        self.store['Tokens']['access_token'] = initialToken
        self.store['Tokens']['refresh_token'] = self.refreshToken
        self.store['refresh_timestamp'] = int(0)
        self.store['last_pin_used'] = ''
        self.store['opmode'] = ''
        self.store['logFilter'] = ''
        # if there is a refreshToken, try to use that
        if self.refreshToken != initialToken:
            if write:
                self.set_authState('init')
            else:
                self.store['authState'] = 'init'

    # load store from file, initialize store structure if no file exists
    def load_store(self):
        try:
            with open(self.storeFile + '.json', 'r', encoding='utf-8') as tf:
                self.store = json.load(tf)
            if 'Tokens' not in self.store:
                self._infoLog('i', "load_store: Tokens missing, calling init_store")
                self.init_store(True)
            self._infoLog('i', "load_store: authState=    " + self.store['authState'])
            self._infoLog('i', "load_store: refresh_token=    " + self.store['Tokens']['refresh_token'])
            self._infoLog('i', "load_store: self.refreshToken=" + self.refreshToken)
        except FileNotFoundError:
            self.log.warning("init: store file not found, try token refresh")
            # try to refresh Token to avoid problem at 1st connect
            try:
                self.Tokens = self.reconnect(True)
                if 'refresh_token' in self.Tokens:
                    self.store['Tokens'] = self.Tokens
                    self.refreshToken = self.Tokens['refresh_token']
                    self.write_store()
                else:
                    self.log.warning("init: token refresh failed, Full Authentication required")
                    self.init_store(True)
                    self.set_authState('init')
            except Exception as e:
                self.log.exception('load_store_file - reconnect failed' + str(e))
            return
        except Exception as e:
            self._infoLog('i', "init: loading stored data failed, file: " +
                          self.storeFile + ", error=" + str(e))
            self.init_store(True)
            return
        return

    # write store file
    def write_store(self):
        # make sure there is a refresh_token in store
        if 'refresh_token' not in self.store['Tokens']:
            self._infoLog('i', "write_store: reset refresh_token to initialToken")
            self.store['Tokens']['refresh_token'] = initialToken

        try:
            with open(self.storeFile + '.json', 'w', encoding='utf-8') as tf:
                json.dump(self.store, tf, indent=4)
        except Exception as e:
            self._infoLog('i', "write_store_file: Exception " + str(e))

        # check if refreshToken has changed and needs to be stored in mqtt?
        if self.refreshTokenMQTT != self.store['Tokens']['refresh_token']:
            self.refreshTokenMQTT = self.store['Tokens']['refresh_token']

            confDict = self.conf.__dict__
            if self.write_store_count == 0:
                # confDict.pop('name')    # no longer required
                confDict['configuration'] = self.conf.configuration.__dict__
            self.su.write_token_mqtt(
                "openWB/set/vehicle/" + self.vehicle + "/soc_module/config",
                self.refreshTokenMQTT,
                self.opmode,
                self.conf.__dict__)
            self.write_store_count += 1
            self._infoLog('i', "write_store: refreshTokenMQTT=   " + self.refreshTokenMQTT +
                          ", write_store_count=" + str(self.write_store_count))
        self._infoLog('i', "write_store: refresh_token_store=" + self.store['Tokens']['refresh_token'])
        return

# password authentication functions
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
            response = self.session.get(url, headers=headers, verify=SSL_VERIFY_AUTH)
            soup = bs4.BeautifulSoup(response.text, 'html.parser')

            for cd in soup.findAll(text=True):
                if "CDATA" in cd:
                    self._infoLog('u', "get_resume: cd.CData= " + str(cd))
                    for w in cd.split(','):
                        if w.find("const initialState = ") != -1:
                            iS = w
            if iS:
                js = iS.split('{')[1].split('}')[0].replace('\\', '').replace('\\"', '"').replace('""', '"')
                self.resume = js[1:len(js)-1].split(':')[1][2:]
            self._infoLog('u', "get_resume: resume = " + self.resume)
        except Exception:
            self.log.exception('get_resume')
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
            response = self.session.post(url, headers=headers, data=data, verify=SSL_VERIFY_AUTH)
            self._infoLog('u', "login: status_code = " + str(response.status_code))
            if response.status_code >= 400:
                self.log.error("login: failed, status_code = " + str(response.status_code) +
                               ", check username/password")
                token = ""
            else:
                result_json = json.loads(str(bs4.BeautifulSoup(response.text, 'html.parser')))
                self._infoLog('U', "login: result_json:\n" + json.dumps(result_json))
                token = result_json['token']
                self._infoLog('u', "login: token = " + token)
        except Exception:
            self.log.exception('login')
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
            response = self.session.post(url, headers=headers, data=data, verify=SSL_VERIFY_AUTH)
            code = response.url.split('?')[1].split('=')[1]
            self._infoLog('U', "get_code: code=" + code)
        except Exception:
            self.log.exception("get_code")
        return code

    # get Tokens
    def get_tokens(self) -> dict:
        self.method += " 3-full (re)connect"
        if self.password != "" and self.password is not None:
            self.resume = self.get_resume()
            self.token = self.login()
            if self.token == "":
                self.log.error("get_tokens: Login failed - check username/password")
                return {}
            code = self.get_code()
            if code == "":
                self.log.warning("get_tokens: get_code failed")
                return {}
        else:
            # reconnect via 2FA
            self.set_authState('init')
            self.loop = True
            self.log.warning("get_tokens failed, password empty: initiate 2FA process")
            return {}

        url = TOKEN_URL
        headers = {
            "Accept": ACCEPT,
            "User-Agent": USER_AGENT_OAUTH,
            "Accept-Language": ACCEPT_LANGUAGE,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = "grant_type=authorization_code&code=" + code + "&code_verifier=" + self.code_verifier +\
               "&redirect_uri=" + REDIRECT_URI + "&client_id=" + CLIENT_ID

        try:
            response = self.session.post(url, headers=headers, data=data, verify=SSL_VERIFY_AUTH)
            Tokens = json.loads(response.text)
            if not Tokens['access_token']:
                self.log.warning("get_tokens: no access_token found")
                Tokens = {}
            else:
                self._infoLog('U', "Tokens=\n" + json.dumps(Tokens, indent=4))
                self.set_authState('authenticated')
        except Exception:
            self.log.exception('get_tokens')
        return Tokens

    # functions used by password and 2FA
    # refresh tokens
    def refresh_tokens(self) -> dict:
        self.method += " 2-refresh_tokens"
        url = TOKEN_URL
        newTokens = {}
        if self.refreshToken != "" and self.refreshToken is not None:
            rt = self.refreshToken
            self._infoLog('t', "refresh_token: old_refresh_token_self.refreshToken=" + rt)
        else:
            rt = self.store['Tokens']['refresh_token']
            self._infoLog('t', "refresh_token: old_refresh_token_store=" + rt)
        headers = {
            "Accept": ACCEPT,
            "User-Agent": USER_AGENT_OAUTH,
            "Accept-Language": ACCEPT_LANGUAGE,
            "Content-Type": CONTENT_TYPE_OAUTH
        }
        if self.password == '':
            data = {'grant_type': 'refresh_token', 'refresh_token': rt}
            self._infoLog('t', "refresh_token: rt=" + rt)
        else:
            data = "grant_type=refresh_token&client_id=" + CLIENT_ID + "&refresh_token=" + rt
        try:
            self._infoLog('T', "refresh_token-post: url=" + url +
                          ", data=" + json.dumps(data, indent=4) +
                          ", headers=" + json.dumps(headers, indent=4))
            response = self.session.post(url,
                                         headers=headers,
                                         data=data,
                                         verify=SSL_VERIFY_AUTH,
                                         allow_redirects=False,
                                         timeout=(30, 30))
            self._infoLog('T', "refresh_tokens result: " + str(response.status_code) + " - " + str(response.text))

            newTokens = json.loads(response.text)
            if 'error' in newTokens and newTokens['error'] == 'unauthorized':
                self.log.warning("refresh_tokens: error: " + newTokens['error'] + ', ' + newTokens['error_description'])
            if 'access_token' not in newTokens:
                self._infoLog('t', "refresh_tokens: new access_token not found")
                newTokens['access_token'] = ""
            if 'refresh_token' not in newTokens:
                self._infoLog('t', "refresh_tokens: new refresh_token not found")
                newTokens['refresh_token'] = ""
            self._infoLog('T', "refresh_tokens: newTokens=\n" + json.dumps(newTokens, indent=4))
        except requests.exceptions.HTTPError as e:
            self.log.warning("refresh_tokens HTTPError: " + str(e.response.status_code) + " - " + str(e.response.text))
        except Exception:
            self.log.exception('refresh_tokens')
            newTokens['access_token'] = ""
            newTokens['refresh_token'] = ""
        if 'refresh_token' not in newTokens:
            self.log.error("refresh_token: new Token not delivered")
            newTokens['refresh_token'] = 'refresh failed'
        self._infoLog('t', "refresh_token: new_refresh_token=" + newTokens['refresh_token'])
        return newTokens

    # reconnect to Server
    def reconnect(self, force: bool) -> dict:
        # check if we have a refresh token and last refresh was more then 1h ago (3600s)
        if 'refresh_token' in self.store['Tokens']:
            now = int(time.time())
            secs_since_refresh = now - self.store['refresh_timestamp']
            if secs_since_refresh > TOKENS_REFRESH_THRESHOLD or force:
                # try to refresh tokens
                self.set_authState('tokenRequested')
                self._infoLog('t', "reconnect: call refresh_tokens")
                new_tokens = self.refresh_tokens()
                self._infoLog('T', "reconnect: refresh_tokens result=" + json.dumps(new_tokens, indent=4))
                self.store['refresh_timestamp'] = int(time.time())
                _ref = True
            else:
                # keep existing tokens
                self._infoLog('t', "reconnect: keep existing Tokens")
                return self.store['Tokens']
        else:
            self.log.error("reconnect: refresh_token not found in self.store['Tokens']=" +
                           json.dumps(self.store['Tokens'], indent=4))
            new_tokens = {'refresh_token': '', 'access_token': ''}
            _ref = False
        self._infoLog('T', "reconnect: new_tokens=" + json.dumps(new_tokens, indent=4))
        if 'access_token' not in new_tokens or new_tokens['access_token'] == '':
            if _ref:
                self.log.warning("reconnect: refresh access_token failed, try full reconnect")
            # check if password not empty call get_tokens, else call 2fa
            Tokens = self.get_tokens()
        else:
            self._infoLog('t', "reconnect: refresh token successful")
            Tokens = self.store['Tokens']   # replace expired access and refresh token by new tokens
            for key in new_tokens:
                Tokens[key] = new_tokens[key]
                self._infoLog('T', "reconnect: replace Tokens[" + key + "], new value: " + str(Tokens[key]))
            self.set_authState('authenticated')

        if 'refresh_token' not in Tokens:
            self.log.error("reconnect: failed, Tokens=" + json.dumps(Tokens, indent=4))
            Tokens['refresh_token'] = 'reconnect-token failed'
        self._infoLog('T', "reconnect: refresh_token=" + Tokens['refresh_token'])
        return Tokens

    # 2fa authentication functions
    # send request for new pin to oauth server
    def request_pin(self, email: str, nonce: str):
        self._infoLog('u', "Start request_pin: email=" + email + ", nonce=" + nonce)

        #   "Accept-Language": ACCEPT_LANGUAGE,
        #   "Accept-Language": "de-DE;q=1.0",
        #   "device-id": str(uuid.uuid4()),
        #   "X-Requestid": str(uuid.uuid4()),
        #   "X-Authmode": "KEYCLOAK"
        headers = {
            "Host": "bff.emea-prod.mobilesdk.mercedes-benz.com",
            "Ris-Os-Name": RIS_OS_NAME,
            "Ris-Os-Version": RIS_OS_VERSION,
            "Ris-Sdk-Version": RIS_SDK_VERSION,
            "X-Locale": X_LOCALE,
            "X-Trackingid": str(uuid.uuid4()),
            "X-Sessionid": str(uuid.uuid4()),
            "User-Agent": WEBSOCKET_USER_AGENT,
            "Content-Type": CONTENT_TYPE,
            "X-Applicationname": X_APPLICATIONNAME_ECE,
            "Accept": ACCEPT,
            "Accept-Encoding": "gzip, deflate, br",
            "Ris-Application-Version": RIS_APPLICATION_VERSION
        }

        url = STATUS_URL_MERCEDES + "/v1/config"
        self._infoLog('U', "request_pin-get: url=" + url +
                      ", headers=" + json.dumps(headers, indent=4))
        response1 = self.session.get(url, headers=headers)
        self._infoLog('U', "Result request_pin get: " + str(response1))

        url = STATUS_URL_MERCEDES + "/v1/login"
        d = {
             "emailOrPhoneNumber": self.username,
             "countryCode": self._country_code,
             "nonce": nonce
        }
        data = json.dumps(d)

        self._infoLog('U', "request_pin-post: url=" + url +
                      ", data=" + json.dumps(data, indent=4) +
                      ", headers=" + json.dumps(headers, indent=4))
        response = self.session.post(url, data=data, headers=headers)
        self._infoLog('u', "Result request_pin post: " + str(response))
        self.set_authState('pinRequested')
        return response

    # request new token set using pin
    def request_new_token_set(self, user_input=None):
        errors = {}
        nonce = self.store['nonce']
        self.set_authState('tokenRequested')
        self.store['last_pin_used'] = self.pin
        try:
            self._infoLog('t', "calling request_access_token")
            result = self.request_access_token(self.username, self.pin, nonce)
        except Exception as error:
            errors = error
            self.log.error("Request token error: %s", errors)
        if not errors:
            self._infoLog('t', "Token received: " + str(result))

    # authenticate: request pin and get tokens
    def authenticate(self):
        errors = {}
        nonce = str(uuid.uuid4())
        user_input = {}
        user_input["nonce"] = nonce

        try:
            self._infoLog('u', "authenticate: calling request_pin")
            response = self.request_pin(self.username, nonce)
            self._infoLog('u', "authenticate: request_pin done, response=" + str(response))
            self._infoLog('u', "authenticate: response.status_code = " + str(response.status_code))
            if response.status_code > 200:
                errors["request_pin"] = "Authentication error " + str(response.status_code)
        except Exception as error:
            errors = error
            self.log.error("authenticate: Request PIN error: %s", errors)

    # request_access_token - part of 2FA process
    def request_access_token(self, email: str, pin: str, nonce: str):
        self._infoLog('t', "enter request_access_token: email=" + email + ", pin=" + pin + ", nonce=" + nonce)
        self.method += " 3-request_access_token"
        url = TOKEN_URL
        encoded_email = urllib.parse.quote_plus(email, safe="@")

        data = (
            "client_id=" + LOGIN_APP_ID +
            "&grant_type=password&username=" + encoded_email +
            "&password=" + nonce + ":" + pin +
            "&scope=" + SCOPE
        )

        headers = {
            "X-Applicationname": X_APPLICATIONNAME_ECE,
            "Ris-Application-Version": RIS_APPLICATION_VERSION,
            "Content-Type": CONTENT_TYPE_OAUTH,
            "Stage": "prod",
            "X-Device-Id": str(uuid.uuid4()),
            "X-Request-Id": str(uuid.uuid4())
        }
        self._infoLog('T', "request_access_token-post: url=" + url +
                      ", data=" + json.dumps(data, indent=4) +
                      ", headers=" + json.dumps(headers, indent=4))
        try:
            token_info = self.session.post(url, data=data, headers=headers)
            self._infoLog('t', "request_access_token.status_code = " + str(token_info.status_code))
            Tokens = json.loads(token_info.text)
            if not Tokens['access_token']:
                self.log.warning("request_access_token failed")
                return None
            self._infoLog('t', "Tokens=\n" + json.dumps(Tokens, indent=4))
            self.store['Tokens'] = Tokens

            if token_info is not None:
                ts = int(time.time())
                self.store['refresh_timestamp'] = ts
                self.store['refresh_time'] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                self.set_authState('authenticated')
                self.write_store()
                return token_info
        except Exception as e:
            self.log.exception("request_access_token exception: " + str(e))
        return None

    # REST API
    # get Soc,range of Vehicle
    def get_status(self, vin: str) -> int:
        soc = 0
        range = 0
        res_json = "invalid response"
        self.method += " 1-get_status"
        url = STATUS_URL + "/seqc/v0/vehicles/" + vin + "/refresh-data"

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
            response = self.session.get(url, headers=headers, verify=SSL_VERIFY_STATUS)
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
                    self._infoLog('r', "get_status: result json:\n" + res_json)
                except Exception:
                    soc = -1
                    range = 0.0
            elif 'error' in res and res['error'] == 'unauthorized':
                self.log.warning("get_status: access_token expired - try refresh")
                self._infoLog('r', "get_status: error - result json:\n" + res_json)
                soc = -1
                range = 0.0

        except requests.exceptions.HTTPError as e:
            self.log.warning("get_status: authentication by access_token failed: " + str(e.response.status_code))
            self._infoLog('r', "get_status HTTPError: " + str(e.response.status_code) + " - " + str(e.response.text))
        except Exception as e:
            self.log.warning("get_status: authentication by access_token failed: " + str(e.response.status_code))
            self._infoLog('r', "get_status Exception: " + str(e.response.status_code) + " - " + str(e.response.text))
            res = json.loads(e.response.text)
            soc = -1
            range = 0.0
        if "Vehicle not found" in res_json:
            soc = -2
            range = 0.0
        return soc, range

    # password auth (password != ""): fetch soc in 3 stages:
    #   1. get_status via stored access_token
    #   2. if expired: refresh_access_token using id and refresh token, then get_status
    #   3. if refresh token expired: login, get tokens, then get_status
    async def _fetch_soc(self) -> Union[int, float]:
        if self.password != "" and self.password is not None:
            self.set_authState('authenticated')
            self._infoLog('f', "fetch_soc: password=" + str(self.password) + ", set authState to authenticated")

        self._infoLog('f', "fetch_soc/start: username=" + str(self.username) +
                      ", password=" + str(self.password) +
                      ", pin=" + str(self.pin) +
                      ", vin=" + str(self.vin) +
                      ", useWebSocket=" + str(self.useWebSocket) +
                      ", refreshToken=" + str(self.refreshToken) +
                      ", vehicle=" + str(self.vehicle) +
                      ", authState=" + str(self.store['authState']))

        soc = -1
        range = 0.0
        self.soc_ts = "n/a"
        self.loop = True
        cnt = 1
        while self.loop:
            if self.store['authState'] == 'authenticated':
                self.loop = False
                self.load_ws_store(self.vin)

                if self.useWebSocket is True and self.ws_store['soc'] != -1:
                    self.method += " 1-websocket"
                    soc = int(self.ws_store['soc'])
                    range = float(self.ws_store['range'])
                    self.soc_ts = self.ws_store['ws_soc_ts']
                else:
                    try:
                        if 'refresh_token' in self.store['Tokens']:
                            self.store['Tokens'] = self.reconnect(False)
                        if 'access_token' in self.store['Tokens']:
                            soc, range = self.get_status(self.vin)
                            if soc >= 0:
                                self._infoLog('f', "fetch_soc: 1st attempt successful")
                            else:
                                self._infoLog('f', "fetch_soc: 1st attempt failed - soc=" + str(soc))

                        if soc == -1:
                            self.set_authState('accessTokenExpired')
                            self._infoLog('f', "fetch_soc: (re)connecting ...")
                            self.store['Tokens'] = self.reconnect(True)
                            if 'access_token' in self.store['Tokens']:
                                soc, range = self.get_status(self.vin)
                                if soc >= 0:
                                    self._infoLog('f', "fetch_soc: 2nd attempt successful")
                                else:
                                    self.log.warning("fetch_soc: 2nd attempt failed - soc=" + str(soc))
                                    range = 0.0
                                    soc = 0
                            else:
                                self.log.error("fetch_soc: (re-)connect failed")
                                soc = 0
                                range = 0.0
                        elif soc == -2:
                            self.log.error("get_status failed, verify VIN ...")
                            soc = 0
                            range = 0.0

                    except Exception:
                        self.log.warning("fetch_soc: exception, (re-)connecting ...")
                        self.store['Tokens'] = self.reconnect(True)
                        if 'access_token' in self.store['Tokens']:
                            soc, range = self.get_status(self.vin)

                    if self.store['Tokens'] != self.oldTokens:
                        self._infoLog('f', "fetch_soc: tokens changed, store token file")
                        self.write_store()

            # authState == pinRequested and pin != last_pin_used: get new token set
            elif self.store['authState'] == 'pinRequested':

                if 'last_pin_used' not in self.store:
                    self.store['last_pin_used'] = ''

                self._infoLog('f', 'fetch_soc/pinRequested: old_pin = ' + self.store['last_pin_used'] +
                              ', pin=' + self.pin)
                if self.store['last_pin_used'] != self.pin:
                    self._infoLog('f', 'fetch_soc/pinRequested: call request_new_token_set')
                    self.request_new_token_set()
                    self.write_store()
                    soc = -1
                    range = 0.0
                else:
                    self.log.warning('fetch_soc/pinRequested: waiting for new pin in configuration')
                    soc = -1
                    range = 0.0
                if self.store['authState'] == 'authenticated':
                    self.loop = True
                else:
                    self.loop = False

            # authState == init: request pin required
            elif self.store['authState'] == 'init':
                self.loop = False
                if self.password == "" or self.password in None:
                    if self.pin == "000000":
                        self._infoLog('f', 'fetch_soc/init: request_pin')
                        self.store['nonce'] = str(uuid.uuid4())
                        self.request_pin(self.username, self.store['nonce'])
                        self.write_store()
                        soc = -1
                        range = 0.0
                    else:
                        self.log.warning('smartEQ: Bitte führe eine (neue) 2-Factor-Authentication durch.')
                        self.log.warning('smartEQ: Öffne die Fahrzeug-SOC-Konfiguration' +
                                         ' und befolge die Anweisungen (?).')
                else:
                    self._infoLog('f', 'fetch_soc/init: reconnect')
                    self.store['Tokens'] = self.reconnect(True)
            # looks like an unexpected state, set to init
            else:
                self._infoLog('f', "fetch_soc: unexpected authState " + self.store['authState'] +
                              ", restart with init ...")
                self.set_authState('init')

            self._infoLog('f', 'fetch_soc/loop: cnt=' +
                          str(cnt) + ', soc=' + str(soc) +
                          ', authState=' + self.store['authState'])
            cnt += 1
        self.log.info(" SOC/Range: " + str(soc) + '%/' + str(range) +
                      '@' + self.soc_ts +
                      ', Method: ' + self.method)

        return soc, range, self.soc_ts

    # web socket section ws_
    # this section implements the websocket interface to mbapi
    # the interface runs in a separate thread wsThread
    # ws_store is used to transfer soc/range to main soc thread
    def init_ws_store(self, vin: str):
        self.ws_store = {}
        self.ws_store['vin'] = vin
        self.ws_store['soc'] = int(-1)
        self.ws_store['range'] = int(-1)
        self.ws_store['ws_soc_ts'] = "na"
        self.ws_store['ws_ts'] = int(0)
        self.ws_store['ws_connect_time'] = int(0)

    def load_ws_store(self, vin: str):
        try:
            tn = self.ws_fname(vin)
            with open(tn, 'r', encoding='utf-8') as tf:
                self.ws_store = json.load(tf)
        except FileNotFoundError:
            self.log.warning("init: ws_store file not found")
            self.init_ws_store(vin)
        except Exception as e:
            self.log.error("init: loading stored ws data failed, file: " +
                           tn + ", error=" + str(e))
            self.init_ws_store(vin)
        return

    def ws_fname(self, vin: str):
        return self.ws_storeFile + '_' + vin + '.json'

    # write ws store file
    def write_ws_store(self, vin: str):
        try:
            tn = self.ws_fname(vin)
            with open(tn, 'w', encoding='utf-8') as tf:
                json.dump(self.ws_store, tf, indent=4)
        except Exception as e:
            self._infoLog('i', "write_ws_store_file: Exception " + str(e))

    # write ws message file
    def write_ws_message(self, mtype: str, _json: str):
        if 'M' in self.logFilter or 'A' in self.logFilter:
            try:
                tn = self.ws_messageFile + '_' + mtype + '.json'
                with open(tn, 'w', encoding='utf-8') as tf:
                    json.dump(_json, tf, indent=4)
            except Exception as e:
                self._infoLog('i', "write_ws_message_file: Exception " + str(e))

    # wait till authState is authenticated
    def ws_wait_for_state_authenticated(self):
        while self.store['authState'] != 'authenticated':
            self._infoLog('w', self.ws_thread_name + ': waiting for authState == authenticated' +
                          ', currently:' + self.store['authState'])
            time.sleep(10)
            self.load_store()

    # wsThread
    def wsThread(self):
        self.store_reload_time = int(time.time())
        self.X_dir = 1
        self.X_ts = int(time.time())
        try:
            # self.vhList, self.vhConfig = self.su._get_vehicleList()   # for test only
            self.vhList = self.su.get_vin_ev_map()
            self.logFilter = self.su._get_logFilter()  # for test only
            self._infoLog('w', self.ws_thread_name + ": soc_smarteq_ws starting")
            self._infoLog('i', "wsThread starting: logFilter=" + self.logFilter)
            now = 0
            self.init_ws_store(self.vin)
            self.load_ws_store(self.vin)
            self.wsError = 0
            # time.sleep(10)
            self.ws_wait_for_state_authenticated()
            # refresh Token to avoid problem at 1st connect
            # self.Tokens = self.reconnect(True)
            # self.store['Tokens'] = self.Tokens
            # self.refreshToken = self.store['Tokens']['refresh_token']
            # self._infoLog('w', self.ws_thread_name + ': write_store, refresh_token =' +
            #               self.Tokens['refresh_token'])
            # self.write_store()

            while True:
                self._infoLog('s', "wsThread main loop: logFilter=" + self.logFilter)

                self.ws_wait_for_state_authenticated()

                if self.wsError > 0:
                    while now + 120 > int(time.time()):
                        self._infoLog('w', 'waiting 2 min before next ws_connect, now=' +
                                      str(now) + ', time=' + str(int(time.time())))
                        time.sleep(30)
                    self.wsError = 0

                self.ws = self.ws_connect()
                now = int(time.time())
                self.ws_connect_time = str(now)
                self._infoLog('w', 'calling ws.run.forever()')
                self.ws.run_forever()

                # if we arrive here connection was lost
                # set ws_soc ws_store to -1 = inactive
                self.ws_soc = str(-1)
                self.ws_range = str(0.0)
                self.ws_soc_ts = 'na'
                self.write_ws_store(self.vin)

                # try to refresh token
                self._infoLog('w', 'pre-reconnect, refresh_token =' +
                              self.store['Tokens']['refresh_token'])
                self.Tokens = self.store['Tokens']
                self.Tokens = self.reconnect(True)
                self.store['Tokens'] = self.Tokens
                self.refreshToken = self.store['Tokens']['refresh_token']
                self._infoLog('w', 'write_store, refresh_token =' +
                              self.Tokens['refresh_token'])
                self.write_store()
        except Exception as e:
            self.log.exception("main loop exception=" + str(e))

    # connect_ws
    def ws_connect(self):
        self._infoLog('w', 'ws_connect: check token')
        if self.store['Tokens']['access_token'] is None:
            self._infoLog('w', 'ws_connect: no access_token found, do 2 Factor Authentication')
            self.step_user()
        if self.store['Tokens']['access_token'] is None:
            self.log.error('ws_connect: still no access token, abort!')
            return -1

        self.assignedVehicles_cnt = 0
        self.debugMessage_cnt = 0
        self.apptwinPendingCommandRequest_cnt = 0
        ws_url = WEBSOCKET_API_BASE

        ws_header = {
            "Authorization": "Bearer " + self.store['Tokens']['access_token'],
            "X-SessionId": str(uuid.uuid4()),
            "X-TrackingId": str(uuid.uuid4()),
            "X-ApplicationName": X_APPLICATIONNAME_ECE,
            "ris-application-version": RIS_APPLICATION_VERSION,
            "ris-os-name": "ios",
            "ris-os-version": RIS_OS_VERSION,
            "ris-sdk-version": RIS_SDK_VERSION,
            "X-Locale": "de-DE",
            "User-Agent": WEBSOCKET_USER_AGENT,
            "Content-Type": "application/json; charset=UTF-8"
        }
        # self.session.cookies.clear()
        self._infoLog('W', "ws_connect: url=" + ws_url +
                      ", ws_header=" + json.dumps(ws_header, indent=4))
        try:
            self.ws_connection = websocket.WebSocketApp(ws_url,
                                                        on_open=self.ws_on_open,
                                                        on_message=self.ws_on_message,
                                                        on_error=self.ws_on_error,
                                                        on_close=self.ws_on_close,
                                                        header=ws_header)
            self._infoLog('W',
                          'ws_connect: post open WebSocketApp, ws_connection=' + repr(self.ws_connection))
            return self.ws_connection
        except Exception as e:
            self.log.exception("ws_connect Exception: " + str(e))
        return self.ws_connection

    def ws_on_open(self, ws):
        self._infoLog('w', "ws_on_open")

    def ws_decode_message(self, res_raw):
        res = vehicle_events_pb2.PushMessage()
        res.ParseFromString(res_raw)
        return res

    def ws_on_message(self, ws, data):
        # reload logFilter every 1 minute to update logFilter in wsThread context
        if self.store_reload_time + 60 < int(time.time()):
            self.store_reload_time = int(time.time())
            self.logFilter = self.su._get_logFilter()
            if self.logFilter is None:
                self.logFilter = ''
            self._infoLog('s', "on_message: logFilter=" + self.logFilter)

        self._infoLog('M', "ws_on_message: data=" + str(data))
        message = self.ws_decode_message(data)
        self._infoLog('M', "ws_on_message: message=" + str(message))
        jmsg = MessageToJson(message)
        self._infoLog('M', "ws_on_message: json message=" + str(jmsg))
        dmsg = json.loads(jmsg)
        messageType = list(dmsg.keys())[0]
        self._infoLog('M', "ws_on_message: messageType = " + str(messageType))
        if messageType == 'vepUpdates':
            self._vin = list(dmsg['vepUpdates']['updates'].keys())[0]
            self._infoLog('M', "ws_on_message _vin found: " + self._vin)
            self.vin = self._vin
            if self.vin == self._vin:
                try:
                    _attr = dmsg['vepUpdates']['updates'][self.vin]['attributes']
                    self.ws_soc = _attr['soc']['intValue']
                    self.ws_range = _attr['rangeelectric']['intValue']
                    self.ws_ts = int(_attr['soc']['timestamp'])
                    self.ws_soc_ts = datetime.datetime.fromtimestamp(self.ws_ts).strftime(date_fmt)
                except Exception as e:
                    self.log.warning("ws_on_message decoding error: %s", e)
                    self.ws_soc = str(-1)
                    self.ws_range = str(0.0)
                    self.ws_soc_ts = 'na'
                self.ws_range_X = self.ws_range
                # simulate a change for testing the set_CarState interface
                if 'X' in self.logFilter and self.X_ts + 120 < int(time.time()):
                    self.X_ts = int(time.time())
                    if self.X_dir == 1:
                        self.ws_range = str(float(self.ws_range) + 0.2)
                        self.X_dir = -1
                    else:
                        self.ws_range = str(float(self.ws_range) - 0.2)
                        self.X_dir = 1

                if self.ws_store['soc'] != self.ws_soc or self.ws_store['range'] != self.ws_range:
                    self.load_store()   # reload store to get actual state
                    self.write_ws_message(messageType, dmsg)
                    self._infoLog('m', "SoC/Range=" + self.ws_soc +
                                  "%/" + self.ws_range +
                                  "KM@" + self.ws_soc_ts)
                    self._infoLog('M', "ws_on_message: data=" + str(data))

                    self._infoLog('M', "ws_on_message: message=" + str(message))
                    self._infoLog('M', "ws_on_message: json message=" + str(jmsg))
                    self.ws_store['vin'] = self._vin
                    self.ws_store['soc'] = self.ws_soc
                    self.ws_store['range'] = self.ws_range
                    self.ws_store['ws_ts'] = self.ws_ts
                    self.ws_store['ws_soc_ts'] = self.ws_soc_ts
                    self.ws_store['connect_time'] = self.ws_connect_time
                    self.write_ws_store(self._vin)
                    if self._vin not in self.vhList:
                        self.vhList = self.su.get_vin_ev_map()
                    if self._vin in self.vhList:
                        ev = self.vhList[self._vin]
                        self.su.set_CarState(ev, self.ws_soc, self.ws_range, self.ws_ts)
                    else:
                        self.log.warning('ws_on_message: VIN not configured as smarteq vehicle: ' + self._vin)
                # restore range if X flag is set for testing
                if 'X' in self.logFilter:
                    self.ws_range = self.ws_range_X
                    self.ws_store['range'] = self.ws_range

                # check time - if connect is more than TOKENS_REFRESH_THRESHOLD ago, stop connection
                now = int(time.time())
                if now > int(self.ws_connect_time) + TOKENS_REFRESH_THRESHOLD_WS:
                    self._infoLog('m', "ws_on_message: close connection")
                    ws.keep_running = False
            else:
                self.log.warning("ws_on_message: wrong VIN, continue listening")
        elif messageType == 'assignedVehicles':
            if self.assignedVehicles_cnt == 0:
                self.assignedVehicles_cnt += 1
                self.write_ws_message(messageType, dmsg)
                self._vins = list(dmsg['assignedVehicles']['vins'])
                for ivin in self._vins:
                    self._infoLog('i', "ws_on_message: assignedVehicles: " + ivin)
                    tn = self.ws_fname(ivin)
                    if not os.path.exists(tn):
                        # ws file for vin does not extst. create new
                        self.init_ws_store(ivin)
                        self.write_ws_store(ivin)
        elif messageType == 'debugMessage':
            if self.debugMessage_cnt == 0:
                self.debugMessage_cnt += 1
                self.write_ws_message(messageType, dmsg)
        elif messageType == 'apptwinPendingCommandRequest':
            if self.apptwinPendingCommandRequest_cnt == 0:
                self.apptwinPendingCommandRequest_cnt += 1
                self.write_ws_message(messageType, dmsg)
        else:
            self.write_ws_message(messageType, dmsg)

    def ws_on_error(self, ws, error):
        self.log.error("ws_on_error: " + str(error))
        try:
            ws.close()
        except Exception as e:
            self._infoLog('w', "ws_on_error: close exception: " + ", error=" + str(e))
        self.ws_soc = str(-1)
        self.ws_range = str(0.0)
        self.ws_soc_ts = 'na'
        self.write_ws_store(self.vin)
        self.wsError = 1

    def ws_on_close(self, ws, status_code, message):
        self._infoLog('w', "ws_on_close, status_code=" + str(status_code) +
                      ", message=" + str(message))
        self.ws_soc = str(-1)
        self.ws_range = str(0.0)
        self.ws_soc_ts = 'na'
        self.write_ws_store(self.vin)


def fetch_soc(conf: SmartEQ, vehicle: int) -> CarState:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = Api(conf, vehicle)
    soc, range, soc_ts = loop.run_until_complete(a._fetch_soc())

    return soc, range, soc_ts
