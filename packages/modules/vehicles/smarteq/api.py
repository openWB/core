#!/usr/bin/env python3

import logging
from typing import Union
import asyncio
import json
from modules.common.store import RAMDISK_PATH
from modules.vehicles.smarteq.config import SmartEQ
import requests
import bs4
import pkce
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


class api:

    def __init__(self, vehicle: int):
        self.log = logging.getLogger("soc."+__name__)
        # LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
        # logging.basicConfig(level=LOGLEVEL)
        self.session = requests.session()
        self.Tokens = {}
        self.tokensFile = str(RAMDISK_PATH) + '/soc_smarteq_Token_vh_' + str(vehicle)
        self.code_verifier, self.code_challenge = pkce.generate_pkce_pair()
        self.code_challenge_method = "S256"

        try:
            tf = open(self.tokensFile, "rb")
            self.Tokens = pickle.load(tf)
            tf.close()
            self.log.debug("Tokens loaded" + json.dumps(self.Tokens))
        except Exception as e:
            self.log.exception("Tokens load failed" + str(e))
            self.Tokens = {}

    def set_credentials(self, username: str, password: str):
        self.username = username
        self.password = password

    def set_vin(self, vin: str):
        self.vin = vin

    def set_chargepoint(self, chargepoint: str):
        self.chargepoint = chargepoint

    # ===== step1 get resume ======
    def get_resume(self) -> str:

        response_type = "code"
        url1 = OAUTH_URL + '?client_id=' + CLIENT_ID + '&response_type=' + response_type + '&scope=' + SCOPE
        url1 = url1 + '&redirect_uri=' + REDIRECT_URI
        url1 = url1 + '&code_challenge=' + self.code_challenge + '&code_challenge_method=' + self.code_challenge_method
        headers1 = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": ACCEPT_LANGUAGE,
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_1 like Mac OS X)\
            AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        }

        try:
            response1 = self.session.get(url1, headers=headers1)
            # self.log.debug("response1.status_code = " + str(response1.status_code))
            soup = bs4.BeautifulSoup(response1.text, 'html.parser')
            for cd in soup.findAll(text=True):
                if "CDATA" in cd:
                    for w in cd.split(','):
                        if w.find("const initialState = ") != -1:
                            iS = w
            if iS:
                js = iS.split('{')[1].split('}')[0].replace('\\', '').replace('\\"', '"').replace('""', '"')
                self.resume = js[1:len(js)-1].split(':')[1][2:]
            # self.log.debug("Step1 get_resume: resume = " + self.resume)
        except Exception as e:
            self.log.exception('Step1 get_resume Exception: ' + str(e))
        return self.resume

    # step2: login to website, return token
    def login(self) -> str:

        url3 = LOGIN_URL + "/pass"
        headers3 = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_1 like Mac OS X)\
            AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": LOGIN_URL,
            "Accept-Language": ACCEPT_LANGUAGE
        }
        d = {}
        d['username'] = self.username
        d['password'] = self.password
        d['rememberMe'] = 'true'
        data3 = json.dumps(d)

        try:
            response3 = self.session.post(url3, headers=headers3, data=data3)
            # self.log.debug("response3.status_code = " + str(response3.status_code))
            # self.log.debug("response3.text = " + str(response3.text))
            result_json = json.loads(str(bs4.BeautifulSoup(response3.text, 'html.parser')))
            # self.log.debug("Step3 result_json:\n" + json.dumps(result_json))
            token = result_json['token']
            # self.log.debug("login - step3 - get token = " + token)
        except Exception as e:
            self.log.exception('Step3 Exception: ' + str(e))
        return token

    # get code
    def get_code(self, token: str) -> str:
        url4 = BASE_URL + '/' + self.resume
        headers4 = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5_1 like Mac OS X)\
            AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "Referer": LOGIN_URL,
            "Accept-Language": ACCEPT_LANGUAGE,
        }
        d = {}
        d['token'] = token
        data4 = json.dumps(d)

        try:
            response4 = self.session.post(url4, headers=headers4, data=data4)
            code = response4.url.split('?')[1].split('=')[1]
            # self.log.debug("login - step4 - get code = " + code)
        except Exception as e:
            self.log.exception("Step4 Exception: " + str(e))
        return code

    # get Tokens
    def get_Tokens(self, code: str) -> dict:
        url5 = TOKEN_URL
        headers5 = {
            "Accept": "*/*",
            "User-Agent": "sOAF/202108260942 CFNetwork/978.0.7 Darwin/18.7.0",
            "Accept-Language": ACCEPT_LANGUAGE,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data5 = "grant_type=authorization_code&code=" + code + "&code_verifier=" + self.code_verifier +\
                "&redirect_uri=" + REDIRECT_URI + "&client_id=" + CLIENT_ID

        try:
            response5 = self.session.post(url5, headers=headers5, data=data5)
            # self.log.debug("response5.status_code = " + str(response5.status_code))
            Tokens = json.loads(response5.text)
            if not Tokens['access_token']:
                self.log.warn("no access_token found")
                return {}
            # self.log.debug("Tokens=\n" + json.dumps(Tokens, indent=4))
        except Exception as e:
            self.log.exception("Step5 Exception: " + str(e))
        return Tokens

    # reconnect to Server
    def reconnect(self) -> dict:
        token = self.login()
        if not token:
            self.log.error("Login failed, token empty - Abort")
            return {}

        code = self.get_code(token)
        self.Tokens = self.get_Tokens(code)

        tf = open(self.tokensFile, "wb")
        pickle.dump(self.Tokens, tf)
        tf.close()

        return self.Tokens

    # get_status -> soc, range of Vehicle
    def get_status(self, vin: str) -> Union[int, float]:
        url7 = STATUS_URL + "/seqc/v0/vehicles/" + vin +\
               "/init-data?requestedData=BOTH&countryCode=DE&locale=de-DE"
        headers7 = {
            "accept": "*/*",
            "accept-language": "de-DE;q=1.0",
            "authorization": "Bearer " + self.Tokens['access_token'],
            "x-applicationname": CLIENT_ID,
            "user-agent": "Device: iPhone 6; OS-version: iOS_12.5.1; App-Name: smart EQ control; App-Version: 3.0;\
            Build: 202108260942; Language: de_DE",
            "guid": GUID
        }

        try:
            response7 = self.session.get(url7, headers=headers7)
            # self.log.debug("response7.status_code = " + str(response7.status_code))
            res7 = json.loads(response7.text)
            soc = int(res7['precond']['data']['soc']['value'])
            range = float(res7['precond']['data']['rangeelectric']['value'])
        except Exception as e:
            self.log.exception("Step7 Exception: " + str(e))
            res7s = json.dumps(res7, indent=4)
            self.log.error("\nget_status result for vin: " + vin + "\n" + res7s)
            soc = -1
            range = 0.0
            if "Vehicle not found" in res7s:
                soc = -2
        return soc, range

    async def _fetch_soc(self,
                         conf: SmartEQ,
                         vehicle: int) -> Union[int, float]:
        self.username = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.vehicle = vehicle

        try:
            try:
                soc = -1
                if self.Tokens['access_token']:
                    soc, range = self.get_status(self.vin)
                    self.log.info("get_status success- valid token")
            except Exception:
                pass

            if soc == -1:
                self.log.error("get_status failed, soc= " + str(soc))
                self.log.error("get_status failed, reconnecting ...")
                self.resume = self.get_resume()
                self.Tokens = self.reconnect()
                soc, range = self.get_status(self.vin)
            elif soc == -2:
                pass

        except Exception as e:
            self.log.exception("get_status failed, reconnecting ..." + str(e))
            self.resume = self.get_resume()
            self.Tokens = self.reconnect()
            soc, range = self.get_status(self.vin)
        return soc, range


def fetch_soc(conf: SmartEQ, vehicle: int) -> Union[int, float]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = api(vehicle)
    soc, range = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range
