#!/usr/bin/env python3

import os
import base64
import json
import random
import requests
import string
import getpass
import urllib

import logging
from modules.common.component_state import CarState
from modules.common.store import RAMDISK_PATH

import uuid
import hashlib
import time

log = logging.getLogger(__name__)

# ---------------Constants-------------------------------------------
auth_server = 'customer.bmwgroup.com'
api_server = 'cocoapi.bmwgroup.com'
APIKey = b'NGYxYzg1YTMtNzU4Zi1hMzdkLWJiYjYtZjg3MDQ0OTRhY2Zh'
USER_AGENT = 'Dart/3.0 (dart:io)'
REGION = '0'        # 0 = rest_of_world
BRAND = 'bmw'       # for auth bmw or mini don't matter
X_USER_AGENT1 = 'android(TQ2A.230405.003.B2);'
X_USER_AGENT2 = ';3.11.1(29513);'
X_USER_AGENT = X_USER_AGENT1 + BRAND + X_USER_AGENT2 + REGION
CONTENT_TYPE = 'application/x-www-form-urlencoded'
CHARSET = 'charset=UTF-8'
BLOCKED403 = 'Block-403'
storeFile = ''


# ------------ Helper functions -------------------------------------
def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout + '.json'
    try:
        f = open(replyFile, 'w', encoding='utf-8')
    except Exception as e:
        log.debug("bmw.dump_json: chmod File" + replyFile + ", exception, e=" + str(e))
        os.system("sudo rm " + replyFile)
        f = open(replyFile, 'w', encoding='utf-8')
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.close()
    try:
        os.chmod(replyFile, 0o666)
    except Exception as e:
        log.debug("bmw.dump_json: chmod replyFile " + replyFile + ", exception, e=" + str(e))
        log.debug("bmw.dump_json: use sudo, user: " + getpass.getuser())
        os.system("sudo chmod 0666 " + replyFile)


def get_random_string(length: int) -> str:
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def create_s256_code_challenge(code_verifier: str) -> str:
    """Create S256 code_challenge with the given code_verifier."""
    data = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("UTF-8")


# initialize store structures when no store is available
def init_store():
    global store
    store = {}
    store['Token'] = {}
    store['expires_at'] = int(0)


# load store from file, initialize store structure if no file exists
def load_store():
    global store
    global storeFile
    try:
        tf = open(storeFile, 'r', encoding='utf-8')
        store = json.load(tf)
        if 'Token' not in store:
            init_store()
        tf.close()
    except FileNotFoundError:
        log.warning("load_store: store file not found, new authentication required")
        store = {}
        init_store()
    except Exception as e:
        log.error("init: loading stored data failed, file: " +
                  storeFile + ", error=" + str(e))
        store = {}
        init_store()


# write store file
def write_store():
    global store
    global storeFile
    try:
        tf = open(storeFile, 'w', encoding='utf-8')
    except Exception as e:
        log.error("write_store_file: Exception " + str(e))
        os.system("sudo rm -f " + storeFile)
        tf = open(storeFile, 'w', encoding='utf-8')
    json.dump(store, tf, indent=4)
    tf.close()
    try:
        os.chmod(storeFile, 0o666)
    except Exception as e:
        os.system("sudo chmod 0666 " + storeFile + ', error=' + str(e))


# ---------------HTTP Function-------------------------------------------
def getHTTP(url: str = '', headers: str = '', cookies: str = '', timeout: int = 30) -> str:
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=timeout)
    except requests.Timeout:
        log.error("bmw.getHTTP: Connection Timeout")
        raise
    except Exception as err:
        log.error("bmw.getHTTP: HTTP Error" + f", {err=}, {type(err)=}")
        raise

    if response.status_code == 200 or response.status_code == 204:
        return response.text
    elif response.status_code == 403:
        return BLOCKED403
    else:
        log.error('bmw.getHTTP: Request failed, StatusCode: ' + str(response.status_code))
        raise RuntimeError


def postHTTP(url: str = '', data: str = '', headers: str = '', cookies: str = '',
             timeout: int = 30, allow_redirects: bool = True,
             authId: str = '', authSec: str = '') -> str:
    try:
        if authId != '':
            response = requests.post(url, data=data, headers=headers, cookies=cookies,
                                     timeout=timeout, auth=(authId, authSec),
                                     allow_redirects=allow_redirects)
        else:
            response = requests.post(url, data=data, headers=headers, cookies=cookies,
                                     timeout=timeout, allow_redirects=allow_redirects)
    except requests.Timeout:
        log.error("bmw.postHTTP: Connection Timeout")
        raise
    except Exception as err:
        log.error("bmw.postHTTP: HTTP Error" + f" {err=}, {type(err)=}")
        raise

    if response.status_code == 200 or response.status_code == 204:
        return response.text
    elif response.status_code == 302:
        return response.headers["location"]
    else:
        log.error('bmw.postHTTP: Request failed, StatusCode: ' + str(response.status_code))
        raise RuntimeError


# ---------------Authentication Function-------------------------------------------
def authStage0(region: str) -> str:
    try:
        id0 = str(uuid.uuid4())
        id1 = str(uuid.uuid4())
        ocp = base64.b64decode(APIKey).decode()
        url = 'https://' + api_server + '/eadrax-ucs/v1/presentation/oauth/config'
        headers = {
            'ocp-apim-subscription-key': ocp,
            'bmw-session-id': id0,
            'x-identity-provider': 'gcdm',
            'x-correlation-id': id1,
            'bmw-correlation-Id': id1,
            'user-agent': USER_AGENT,
            'x-user-agent': X_USER_AGENT}
        response = getHTTP(url, headers)
        cfg = json.loads(response)
    except Exception as err:
        log.error("bmw.authStage0: Authentication stage 0 Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_authStage0')
        raise

    return cfg


def authStage1(url: str,
               username: str,
               password: str,
               code_challenge: str,
               state: str,
               nonce: str) -> str:
    global config
    try:
        headers = {
            'Content-Type': CONTENT_TYPE,
            'user-agent': USER_AGENT,
            'x-user-agent': X_USER_AGENT}
        data = {
            'client_id': config['clientId'],
            'response_type': 'code',
            'scope': ' '.join(config['scopes']),
            'redirect_uri': config['returnUrl'],
            'state': state,
            'nonce': nonce,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'username': username,
            'password': password,
            'grant_type': 'authorization_code'}

        resp = postHTTP(url, data, headers)
        response = json.loads(resp)
        authcode = dict(urllib.parse.parse_qsl(response["redirect_to"]))["authorization"]
    except Exception as err:
        log.error("bmw.authStage1: Authentication stage 1 Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['data'] = data
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_authStage1')
        raise

    return authcode


def authStage2(url: str, authcode1: str, code_challenge: str, state: str, nonce: str) -> str:
    global config
    try:
        headers = {
            'Content-Type': CONTENT_TYPE,
            'user-agent': USER_AGENT,
            'x-user-agent': X_USER_AGENT}
        data = {
            'client_id': config['clientId'],
            'response_type': 'code',
            'scope': ' '.join(config['scopes']),
            'redirect_uri': config['returnUrl'],
            'state': state,
            'nonce': nonce,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'authorization': authcode1}
        cookies = {
            'GCDMSSO': authcode1}

        response = postHTTP(url, data, headers, cookies, allow_redirects=False)
        authcode = dict(urllib.parse.parse_qsl(response.split("?", 1)[1]))["code"]
    except Exception as err:
        log.error("bmw.authStage2: Authentication stage 2 Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['data'] = data
        dmp['cookies'] = cookies
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_authStage2')
        raise

    return authcode


def authStage3(token_url: str, authcode2: str, code_verifier: str) -> dict:
    global config
    try:
        url = token_url
        headers = {
            'Content-Type': CONTENT_TYPE + '; ' + CHARSET}
        data = {
            'code': authcode2,
            'code_verifier': code_verifier,
            'redirect_uri': config['returnUrl'],
            'grant_type': 'authorization_code'}
        authId = config['clientId']
        authSec = config['clientSecret']
        response = postHTTP(url, data, headers, authId=authId, authSec=authSec, allow_redirects=False)
        token = json.loads(response)
    except Exception as err:
        log.error("bmw.authStage3: Authentication stage 3 Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['data'] = data
        dmp['authId'] = authId
        dmp['authSec'] = authSec
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_authStage3')
        raise

    return token


def requestToken(username: str, password: str) -> dict:
    global config
    global method
    try:
        method += ' requestToken'
        config = {}           # initialize to avoid undefined var in exception handling
        code_challenge = {}   # initialize to avoid undefined var in exception handling
        state = {}            # initialize to avoid undefined var in exception handling
        auth_code_1 = {}      # initialize to avoid undefined var in exception handling
        auth_code_2 = {}      # initialize to avoid undefined var in exception handling
        token = {}            # initialize to avoid undefined var in exception handling

        # new: get oauth config from server
        config = authStage0(REGION)
        token_url = config['tokenEndpoint']
        authenticate_url = token_url.replace('/token', '/authenticate')
        code_verifier = get_random_string(86)
        code_challenge = create_s256_code_challenge(code_verifier)
        state = get_random_string(22)
        nonce = get_random_string(22)

        authcode1 = authStage1(authenticate_url, username, password, code_challenge, state, nonce)
        authcode2 = authStage2(authenticate_url, authcode1, code_challenge, state, nonce)
        token = authStage3(token_url, authcode2, code_verifier)
    except Exception as err:
        log.error("bmw.requestToken: Login Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['config'] = config
        dmp['code_challenge'] = code_challenge
        dmp['state'] = state
        dmp['auth_code_1'] = auth_code_1
        dmp['auth_code_2'] = auth_code_2
        dmp['token'] = token
        dump_json(dmp, '/soc_bmw_dump_requestToken')
        raise

    return token


def refreshToken(refreshToken: str) -> dict:
    global config
    global method
    try:
        method += ' refreshToken'
        config = authStage0(REGION)
        url = config['tokenEndpoint']
        headers = {
            'Content-Type': CONTENT_TYPE,
            'user-agent': USER_AGENT,
            'x-user-agent': X_USER_AGENT}
        data = {
            'scope': ' '.join(config['scopes']),
            'redirect_uri': config['returnUrl'],
            'grant_type': 'refresh_token',
            'refresh_token': refreshToken}
        authId = config['clientId']
        authSec = config['clientSecret']
        resp = postHTTP(url, data, headers, authId=authId, authSec=authSec, allow_redirects=False)
        token = json.loads(resp)
    except Exception as e:
        log.error("Login failed, Error=" + str(e))
        raise

    return token


# ---------------Interface Function------------------------------------------------
def requestData(token: str, vin: str) -> dict:
    global method
    try:
        method += ' requestData'
        if vin[:2] == 'WB':
            brand = 'bmw'
        elif vin[:2] == 'WM':
            brand = 'mini'
        else:
            log.error("BMW: Cannot map VIN ' + vin + ' to brand bmw or mini")
            raise RuntimeError

        url = 'https://' + api_server + '/eadrax-vcs/v4/vehicles/state'
        headers = {
            'user-agent': USER_AGENT,
            'x-user-agent': X_USER_AGENT1 + brand + X_USER_AGENT2 + REGION,
            'bmw-vin': vin,
            'Authorization': (token["token_type"] + " " + token["access_token"])}
        body = getHTTP(url, headers)

        retry_count = 3
        while body == BLOCKED403 and retry_count > 0:
            log.warning('requestData: received error 403 (blocked by server) - retry after 3 seconds')
            time.sleep(3)
            retry_count -= 1
            body = getHTTP(url, headers)
        if retry_count == 0:
            log.error('requestData: max retry reached, abort')
            raise

        response = json.loads(body)
    except Exception as err:
        log.error("bmw.requestData: Data Request Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_requestData')
        raise

    return response


# ---------------fetch Function called by core ------------------------------------
def fetch_soc(user_id: str, password: str, vin: str, vehicle: int) -> CarState:
    global method
    global storeFile
    global store
    store = {}
    storeFile = str(RAMDISK_PATH) + '/soc_bmw_vh_' + str(vehicle) + '.json'
    method = ''

    try:
        # try to read store file from ramdisk
        expires_in = -1
        load_store()
        now = int(time.time())
        log.debug('main: store=\n' + json.dumps(store, indent=4))
        # if OK, check if refreshToken is required
        if 'expires_at' in store and \
           'Token' in store and \
           'expires_in' in store['Token'] and \
           'refresh_token' in store['Token']:
            expires_in = store['Token']['expires_in']
            expires_at = store['expires_at']
            token = store['Token']
            log.debug('main0: expires_in=' + str(expires_in) + ', now=' + str(now) +
                      ', expires_at=' + str(expires_at) + ', diff=' + str(expires_at - now))
            if now > expires_at - 120:
                log.debug('call refreshToken')
                token = refreshToken(token['refresh_token'])
                if 'expires_in' in token:
                    expires_in = int(token['expires_in'])
                    expires_at = now + expires_in
                    store['expires_at'] = expires_at
                    store['Token'] = token
                    write_store()
                else:
                    log.error("refreshToken failed, re-authenticate")
                    expires_in = -1
            else:
                expires_in = store['Token']['expires_in']

        # if refreshToken fails, call requestToken
        if expires_in == -1:
            log.debug('call requestToken')
            token = requestToken(user_id, password)

        # compute expires_at and store file in ramdisk
        if 'expires_in' in token:
            if expires_in != int(token['expires_in']):
                expires_in = int(token['expires_in'])
                expires_at = now + expires_in
                store['expires_at'] = expires_at
                store['Token'] = token
                write_store()
        else:
            log.error("requestToken failed")
            store['expires_at'] = 0
            store['Token'] = token
            write_store()
        log.debug('main: token=\n' + json.dumps(token, indent=4))
        data = requestData(token, vin)

        dump_json(data, '/soc_bmw_reply_vehicle_' + str(vehicle))
        soc = int(data["state"]["electricChargingState"]["chargingLevelPercent"])
        range = float(data["state"]["electricChargingState"]["range"])
        lastUpdated = data["state"]["lastUpdatedAt"]
        log.info(" SOC/Range: " + str(soc) + '%/' + str(range) + 'KM@' + lastUpdated + ', method:' + method)

    except Exception as err:
        log.error("bmw.fetch_soc: requestData Error, vehicle: " + str(vehicle) + f" {err=}, {type(err)=}")
        raise
    return CarState(soc, range)
