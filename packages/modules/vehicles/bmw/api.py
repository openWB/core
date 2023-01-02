#!/usr/bin/env python3

from typing import Union
import os
import base64
import json
import random
import requests
import string
import getpass
import urllib

import logging
from modules.common.store import RAMDISK_PATH

log = logging.getLogger("soc."+__name__)

# ---------------Constants-------------------------------------------
auth_server = 'customer.bmwgroup.com'
api_server = 'cocoapi.bmwgroup.com'

client_id = '31c357a0-7a1d-4590-aa99-33b97244d048'
client_password = 'c0e3393d-70a2-4f6f-9d3c-8530af64d552'


def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout
    try:
        f = open(replyFile, 'w', encoding='utf-8')
    except Exception as e:
        log.debug("bmw.dump_json: chmod File" + replyFile + ", exception, e=" + str(e))
        os.system("sudo rm " + replyFile)
        f = open(replyFile, 'w', encoding='utf-8')
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.close()
    try:
        os.chmod(replyFile, 0o777)
    except Exception as e:
        log.debug("bmw.dump_json: chmod replyFile " + replyFile + ", exception, e=" + str(e))
        log.debug("bmw.dump_json: use sudo, user: " + getpass.getuser())
        os.system("sudo chmod 0777 " + replyFile)


# ---------------Helper Function-------------------------------------------
def get_random_string(length: int) -> str:
    letters = string.ascii_letters
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def create_auth_string(client_id: str, client_password: str) -> str:
    auth_string = client_id + ':' + client_password
    auth_bytes = auth_string.encode("ascii")
    b64bytes = base64.b64encode(auth_bytes)
    auth_string = 'Basic ' + b64bytes.decode("ascii")
    return auth_string


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
    else:
        log.error('bmw.getHTTP: Request failed, StatusCode: ' + str(response.status_code))
        raise RuntimeError


def postHTTP(url: str = '', data: str = '', headers: str = '', cookies: str = '',
             timeout: int = 30, allow_redirects: bool = True) -> str:
    try:
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
def authStage1(username: str, password: str, code_challenge: str, state: str) -> str:
    try:
        response = {}     # initialize to avoid undefined var in exception handling
        url = 'https://' + auth_server + '/gcdm/oauth/authenticate'
        userAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) '
        userAgent = userAgent + 'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': userAgent
            }
        scope = 'openid profile email offline_access smacc vehicle_data perseus dlm '
        scope = scope + 'svds cesim vsapi remote_services fupo authenticate_user'
        data = {
            'client_id': client_id,
            'response_type': 'code',
            'scope': scope,
            'redirect_uri': 'com.bmw.connected://oauth',
            'state': state,
            'nonce': 'login_nonce',
            'code_challenge': code_challenge,
            'code_challenge_method': 'plain',
            'username': username,
            'password': password,
            'grant_type': 'authorization_code'}

        response = json.loads(postHTTP(url, data, headers))
        auth_code = dict(urllib.parse.parse_qsl(response["redirect_to"]))["authorization"]
    except Exception as err:
        log.error("bmw.authStage1: Authentication stage 1 Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['data'] = data
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_authStage1')
        raise

    return auth_code


def authStage2(auth_code_1: str, code_challenge: str, state: str) -> str:
    try:
        response = {}      # initialize to avoid undefined var in exception handling
        url = 'https://' + auth_server + '/gcdm/oauth/authenticate'
        userAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) '
        userAgent = userAgent + 'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': userAgent
        }
        scope = 'openid profile email offline_access smacc vehicle_data perseus dlm '
        scope = scope + 'svds cesim vsapi remote_services fupo authenticate_user'
        data = {
            'client_id': client_id,
            'response_type': 'code',
            'scope': scope,
            'redirect_uri': 'com.bmw.connected://oauth',
            'state': state,
            'nonce': 'login_nonce',
            'code_challenge': code_challenge,
            'code_challenge_method': 'plain',
            'authorization': auth_code_1
        }
        cookies = {
            'GCDMSSO': auth_code_1
        }

        response = postHTTP(url, data, headers, cookies, allow_redirects=False)
        auth_code = dict(urllib.parse.parse_qsl(response.split("?", 1)[1]))["code"]
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

    return auth_code


def authStage3(auth_code_2: str, code_challenge: str) -> dict:
    try:
        response = {}      # initialize to avoid undefined var in exception handling
        url = 'https://' + auth_server + '/gcdm/oauth/token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Authorization': create_auth_string(client_id, client_password)}
        data = {
            'code': auth_code_2,
            'code_verifier': code_challenge,
            'redirect_uri': 'com.bmw.connected://oauth',
            'grant_type': 'authorization_code'}

        response = postHTTP(url, data, headers, allow_redirects=False)
        token = json.loads(response)
    except Exception as err:
        log.error("bmw.authStage3: Authentication stage 3 Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['url'] = url
        dmp['headers'] = headers
        dmp['data'] = data
        dmp['response'] = response
        dump_json(dmp, '/soc_bmw_dump_authStage3')
        raise

    return token


def requestToken(username: str, password: str) -> dict:
    try:
        code_challenge = {}   # initialize to avoid undefined var in exception handling
        state = {}            # initialize to avoid undefined var in exception handling
        auth_code_1 = {}      # initialize to avoid undefined var in exception handling
        auth_code_2 = {}      # initialize to avoid undefined var in exception handling
        token = {}            # initialize to avoid undefined var in exception handling
        code_challenge = get_random_string(86)
        state = get_random_string(22)

        auth_code_1 = authStage1(username, password, code_challenge, state)
        auth_code_2 = authStage2(auth_code_1, code_challenge, state)
        token = authStage3(auth_code_2, code_challenge)
    except Exception as err:
        log.error("bmw.requestToken: Login Error" + f" {err=}, {type(err)=}")
        dmp = {}
        dmp['code_challenge'] = code_challenge
        dmp['state'] = state
        dmp['auth_code_1'] = auth_code_1
        dmp['auth_code_2'] = auth_code_2
        dmp['token'] = token
        dump_json(dmp, '/soc_bmw_dump_requestToken')
        raise

    return token


# ---------------Interface Function-------------------------------------------
def requestData(token: str, vin: str) -> dict:
    try:
        response = {}      # initialize to avoid undefined var in exception handling
        if vin[:2] == 'WB':
            brand = 'bmw'
        elif vin[:2] == 'WM':
            brand = 'mini'
        else:
            log.error("bmw.requestData: Unknown VIN, must start with WB or WM")
            raise RuntimeError

        url = 'https://' + api_server + '/eadrax-vcs/v2/vehicles/' + vin + '/state'
        headers = {
            'User-Agent': 'Dart/2.14 (dart:io)',
            'x-user-agent': 'android(SP1A.210812.016.C1);' + brand + ';2.5.2(14945);row',
            'Authorization': (token["token_type"] + " " + token["access_token"])}
        body = getHTTP(url, headers)
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


def fetch_soc(user_id: str, password: str, vin: str, vehicle: int) -> Union[int, float]:

    try:
        token = requestToken(user_id, password)
        data = requestData(token, vin)
        dump_json(data, '/soc_bmw_reply_vehicle_' + str(vehicle))
        soc = int(data["state"]["electricChargingState"]["chargingLevelPercent"])
        range = float(data["state"]["electricChargingState"]["range"])
    except Exception as err:
        log.error("bmw.fetch_soc: requestData Error, vehicle: " + str(vehicle) + f" {err=}, {type(err)=}")
        raise
    return soc, range
