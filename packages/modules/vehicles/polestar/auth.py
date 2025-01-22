import logging
import json
import requests
import os
import re
from datetime import datetime, timedelta
import base64
import hashlib
from modules.common.store import RAMDISK_PATH

AUTH_CLIENT_ID = 'l3oopkc_10'
BASE_URL = 'https://polestarid.eu.polestar.com'
REDIRECT_URI = 'https://www.polestar.com/sign-in-callback'

log = logging.getLogger(__name__)


def b64urlencode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


class PolestarAuth:
    """ base class for Polestar authentication"""

    def __init__(self, username: str, password: str, vin: str) -> None:
        self.username = username
        self.password = password
        self.vin = vin
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.client_session = requests.session()
        self.resume_path = None
        self.code = None
        self.token = None
        self.token_file = str(RAMDISK_PATH)+'/polestar2_token_'+vin+'.json'
        self.token_store: dict = {}
        self.code_verifier = None
        self.oidc_configuration = {}
        self.update_oidc_configuration()

    def update_oidc_configuration(self) -> None:
        result = self.client_session.get(
            BASE_URL+"/.well-known/openid-configuration"
        )
        result.raise_for_status()
        self.oidc_configuration = result.json()

    def delete_token(self) -> None:
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        # remove from ramdisk
        if os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
            except IOError:
                log.error("delete_token:error deleting token store %s", self.token_file)

    def _load_token_from_ramdisk(self) -> None:
        if os.path.exists(self.token_file):
            log.info("_load_token_from_ramdisk:loading from file %s", self.token_file)
            self.token_store = {}
            with open(self.token_file, "r") as tf:
                try:
                    self.token_store = json.load(tf)
                    self.access_token = self.token_store['access_token']
                    self.refresh_token = self.token_store['refresh_token']
                    self.token_expiry = datetime.strptime(self.token_store['token_expiry'], "%d.%m.%Y %H:%M:%S")
                except json.JSONDecodeError as e:
                    log.error("_load_token_from_ramdisk:error loading token store %s:%s",
                              self.token_file, e)

            if 'access_token' not in self.token_store:
                self.access_token = None
            if 'refresh_token' not in self.token_store:
                self.refresh_token = None
            if 'token_expiry' not in self.token_store:
                self.token_expiry = None

    def _save_token_to_ramdisk(self) -> None:
        try:
            tf = open(self.token_file, mode='w', encoding='utf-8')
        except IOError as e:
            log.error("_save_token_to_ramdisk:error saving token store %s:%s", self.token_file, e)
            return
        try:
            json.dump(self.token_store, tf, ensure_ascii=False, indent=4)
        except json.JSONDecodeError as e:
            log.error("_save_token_to_ramdisk:error saving token store %s:%s", self.token_file, e)

    # auth step 3: get token
    def get_auth_token(self) -> str or None:
        # first try to load token from ramdisk
        self._load_token_from_ramdisk()

        if self.token_expiry is not None and self.token_expiry > datetime.now():
            log.info("get_auth_token:using token from file %s", self.token_file)
            return self.access_token
        else:
            log.info("get_auth_token:token from file %s expired. New token required", self.token_file)

        if self.refresh_token is not None:
            # try refresh token
            params = {
                "grant_type": "refresh_token",
                "client_id": AUTH_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "refresh_token": self.refresh_token
            }
            log.info("get_auth_token:using refresh_token to get new token")
        else:
            # first get code, then token
            code = self._get_auth_code()
            if code is None:
                return None

            log.info("get_auth_token:attempting to get new token")
            params = {
                "grant_type": "authorization_code",
                "client_id": AUTH_CLIENT_ID,
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": self.code_verifier,
            }

        # get token
        try:
            result = self.client_session.post(self.oidc_configuration["token_endpoint"],
                                              data=params)

        except requests.RequestException as e:
            log.error("get_auth_token:http error:%s", e)
            self.refresh_token = None
            return None
        if result.status_code != 200:
            log.error("get_auth_token:error:get response:%d", result.status_code)
            self.refresh_token = None
            return None

        result_data = result.json()
        log.info(result_data)

        if result_data['access_token'] is not None:
            self.access_token = result_data['access_token']
            self.refresh_token = result_data['refresh_token']
            self.token_expiry = datetime.now(
            ) + timedelta(seconds=result_data['expires_in'])
            # save tokens to ramdisk
            self.token_store['access_token'] = self.access_token
            self.token_store['refresh_token'] = self.refresh_token
            self.token_store['token_expiry'] = self.token_expiry.strftime("%d.%m.%Y %H:%M:%S")
            self._save_token_to_ramdisk()
        else:
            log.error("get_auth_token:error getting token:no valid data in http response")
            return None

        log.info("get_auth_token:got token:%s", self.access_token)
        return self.access_token

    # auth step 2: get code
    def _get_auth_code(self) -> str or None:
        self.resume_path = self._get_auth_resumePath()
        if self.resume_path is None:
            return None

        params = {
            "grant_type": "authorization_code",
            'client_id': AUTH_CLIENT_ID,
         }
        data = {
            'pf.username': self.username,
            'pf.pass': self.password
        }

        log.info("_get_auth_code:attempting to get new code")
        try:
            result = self.client_session.post(
                BASE_URL+f"/as/{self.resume_path}/resume/as/authorization.ping",
                params=params,
                data=data
            )
        except requests.RequestException as e:
            log.error("_get_auth_code:http error:%s", e)
            return None
        if result.status_code != 200:
            log.error("_get_auth_code:error getting auth code: post response:%d", result.status_code)
            return None
        if re.search(r"ERR", result.request.path_url, flags=re.IGNORECASE) is not None:
            log.error("_get_auth_code:error:check username/password")
            return None
        # get code
        m = re.search(r"code=([^&]+)", result.request.path_url)
        if m is not None:
            code = m.group(1)
            log.info("_get_auth_code:got code %s", code)
        else:
            # try to accept terms and conditions in order to get code
            m = re.search(r"uid=(.+)", result.request.path_url)
            if m is not None:
                uid = m.group(1)
                log.info("_get_auth_code:accept terms and conditions for uid %s", uid)
                data = {"pf.submit": True, "subject": uid}
                result = self.client_session.post(
                    BASE_URL+f"/as/{self.resume_path}/resume/as/authorization.ping",
                    data=data,
                )
            m = re.search(r"code=(.+)", result.request.path_url)
            if m is not None:
                code = m.group(1)
                log.info("_get_auth_code:got code %s", code)
            else:
                code = None
                log.info("_get_auth_code:error getting auth code")

        return code

    # auth step 1: get resumePath
    def _get_auth_resumePath(self) -> str or None:
        # Get Resume Path
        params = {
            "response_type": "code",
            "client_id": AUTH_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "state": self.get_state(),
            "code_challenge": self.get_code_challenge(),
            "code_challenge_method": "S256",
            "scope": "openid profile email customer:attributes"
        }

        log.info("_get_auth_resumePath:attempting to get resumePath")
        try:
            result = self.client_session.get(self.oidc_configuration["authorization_endpoint"],
                                             params=params)
        except requests.RequestException as e:
            log.error("_get_auth_resumePath:http error:%s", e)
            return None
        if result.status_code != 200:
            log.error("_get_auth_resumePath:get response:%d", result.status_code)
            return None
        m = re.search(r"resumePath=([^&]+)", result.url)
        if m is not None:
            resume_path = m.group(1)
            log.info("_get_auth_resumePath:got resumePath %s", resume_path)
        else:
            resume_path = None
            log.info("_get_auth_resumePath:error getting resumePath")

        return resume_path

    @staticmethod
    def get_state() -> str:
        return b64urlencode(os.urandom(32))

    @staticmethod
    def get_code_verifier() -> str:
        return b64urlencode(os.urandom(32))

    def get_code_challenge(self) -> str:
        self.code_verifier = self.get_code_verifier()
        m = hashlib.sha256()
        m.update(self.code_verifier.encode())
        return b64urlencode(m.digest())
