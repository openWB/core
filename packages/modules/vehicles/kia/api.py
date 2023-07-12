#!/usr/bin/env python3

import base64
import json
import uuid
import hashlib
import requests
import urllib.parse as urlparse
from urllib.parse import parse_qs
import time
from typing import Union

import logging
from modules.common.component_state import CarState
from modules.common.store import RAMDISK_PATH

log = logging.getLogger(__name__)

# ---------- constants ----------


def getString(param_id: str, brand: str) -> str:
    if brand == 'kia':
        if param_id == "app_id":
            paramStr = "1518dd6b-2759-4995-9ae5-c9ad4a9ddad1"
        elif param_id == "client_id":
            paramStr = "fdc85c00-0a2f-4c64-bcb4-2cfb1500730a"
        elif param_id == "auth_client_id":
            paramStr = "572e0304-5f8d-4b4c-9dd5-41aa84eed160"
        elif param_id == "gcm_sender_id":
            paramStr = "cF5o4DiiQkaw5wsAkLzYIS:APA91bFB59MltBMK29zI0U2llq" + \
                       "7khbB2jELkNFKMfBCH6KlCPL16pz_dG0fZ4ncvFn1IMT8nfoj" + \
                       "b83JyLiT_skBTXtClHhDCKeRbyPy3yQjCVRC3zTZt--wI7vv4" + \
                       "jD9aknhHhiQsoZoU"
        elif param_id == "basic_token":
            paramStr = "Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA" + \
                       "3MzBhOnNlY3JldA=="
        elif param_id == "stamp_pad":
            paramStr = "C0B4D5C7089D987F027C96015929C70FA9D2B2AA99530CFD0" + \
                       "17E4B243C4BA5C5DED96DEB128EEB5DD3963DFC12432C9073EF"
        elif param_id == "host":
            paramStr = "prd.eu-ccapi.kia.com:8080"
        elif param_id == "base_url":
            paramStr = "https://prd.eu-ccapi.kia.com:8080"
        else:
            raise RuntimeError

    if brand == 'hyundai':
        if param_id == "app_id":
            paramStr = "1eba27d2-9a5b-4eba-8ec7-97eb6c62fb51"
        elif param_id == "client_id":
            paramStr = "6d477c38-3ca4-4cf3-9557-2a1929a94654"
        elif param_id == "auth_client_id":
            paramStr = "64621b96-0f0d-11ec-82a8-0242ac130003"
        elif param_id == "gcm_sender_id":
            paramStr = "414998006775"
        elif param_id == "basic_token":
            paramStr = "Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk" + \
                       "0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5" + \
                       "aVFobUlGampvWTRJcHhzVg=="
        elif param_id == "stamp_pad":
            paramStr = "445B6846AFEF0D726646776865A650C9AEF98E51A474DCB7E" + \
                       "C9B1B67D29C66EAAEF621CA02522A0B80A8087F7A3A7BB0F71B"
        elif param_id == "host":
            paramStr = "prd.eu-ccapi.hyundai.com:8080"
        elif param_id == "base_url":
            paramStr = "https://prd.eu-ccapi.hyundai.com:8080"
        else:
            raise RuntimeError

    return paramStr


def getBrand(vin: str) -> str:
    # Determinate brand based on VIN
    try:
        if vin[:2] == 'KN' or vin[:3] == 'U5Y' or vin[:3] == 'U6Z':
            brand = "kia"
        elif vin[:3] == 'KMH' or vin[:3] == 'TMA':
            brand = "hyundai"
        else:
            brand = ""
            log.error("kia.getBrand: Vehicle WMI unknown")
            raise RuntimeError
    except Exception:
        log.error("kia.getBrand: VIN error", exc_info=True)
        raise

    return brand

# ---------- stamp generation ----------


def getStamp(brand: str) -> str:
    try:
        # Set App-ID and App-ID specific XOR-pad
        app_id = getString("app_id", brand)
        secret_ba = bytearray.fromhex(getString("stamp_pad", brand))

        # Timestamp in ms as string
        nowStr = str(int(time.time()) * 1000)

        # Combine plaintext and convert to bytearray
        plaintext = app_id + ":" + nowStr
        plaintext_ba = bytearray(plaintext.encode())

        # XOR plaintext and key
        stamp_ba = bytes(a ^ b for (a, b) in zip(plaintext_ba, secret_ba))

        # Convert result to base64-string
        stamp_b64_ba = base64.b64encode(stamp_ba)
        stamp = stamp_b64_ba.decode()

    except Exception:
        log.error("kia.getStamp: stamp error", exc_info=True)
        raise

    return stamp

# ---------- HTTP functions ----------


last_cookies = {}
last_url = ""


def getHTTP(url: str = "", headers: str = "", cookies: str = "",
            timeout: int = 30, allow_redirects: bool = True) -> str:
    global last_cookies
    global last_url

    try:
        response = requests.get(url, headers=headers,
                                cookies=cookies, timeout=timeout,
                                allow_redirects=allow_redirects)
    except Exception:
        log.error("kia.getHTTP: HTTP error", exc_info=True)
        raise

    if response.status_code == 200 or response.status_code == 204:
        last_cookies = response.cookies.get_dict()
        return response.text
    elif response.status_code == 302:
        return response.headers['Location']
    else:
        try:
            response_dict = json.loads(response.text)
            if response.status_code == 400 or \
                    response.status_code == 408 or \
                    response.status_code == 503:
                error_string = "[" + response_dict['resCode'] + "] " + \
                               response_dict['resMsg']
            else:
                error_string = "[" + response_dict['errCode'] + "] " + \
                               response_dict['errMsg']
        except Exception:
            error_string = "[XXXX] Unidentified Error" + " " + response.text

        log.debug("kia.getHTTP:Request failed, StatusCode: " +
                  str(response.status_code) + ', Error: ' + error_string)
        raise RuntimeError

    return ""


def putHTTP(url: str = "", data: Union[str, dict] = "",
            headers: str = "", cookies: str = "", timeout: int = 30) -> str:
    try:
        if isinstance(data, dict):
            response = requests.put(url, json=data, headers=headers,
                                    cookies=cookies, timeout=timeout)
        else:
            response = requests.put(url, data=data, headers=headers,
                                    cookies=cookies, timeout=timeout)
    except Exception:
        log.error("kia.putHTTP: HTTP error", exc_info=True)
        raise

    if response.status_code == 200 or response.status_code == 204:
        return response.text
    else:
        try:
            response_dict = json.loads(response.text)
            if response.status_code == 408:
                error_string = "[" + response_dict['resCode'] + "] " + \
                               response_dict['resMsg']
            else:
                error_string = "[" + response_dict['errCode'] + "] " + \
                               response_dict['errMsg']
        except Exception:
            error_string = "[XXXX] Unidentified Error"

        log.debug("kia.putHTTP:Request failed, StatusCode: " +
                  str(response.status_code) + ', Error: ' + error_string)
        raise RuntimeError

    return ""


def deleteHTTP(url: str = "", headers: str = "", cookies: str = "",
               timeout: int = 30) -> None:
    try:
        response = requests.delete(url, headers=headers, cookies=cookies,
                                   timeout=timeout)
    except Exception:
        log.error("kia.putHTTP: HTTP error: " + response, exc_info=True)
        raise

    return


def postHTTP(url: str = "", data: Union[str, dict] = "",
             headers: str = "", cookies: str = "", timeout: int = 30,
             allow_redirects: bool = True) -> str:
    global last_cookies
    global last_url

    try:
        if isinstance(data, dict):
            response = requests.post(url, json=data, headers=headers,
                                     cookies=cookies, timeout=timeout,
                                     allow_redirects=allow_redirects)
        else:
            response = requests.post(url, data=data, headers=headers,
                                     cookies=cookies, timeout=timeout,
                                     allow_redirects=allow_redirects)
    except Exception:
        log.error("kia.postHTTP: HTTP error", exc_info=True)
        raise

    if response.status_code == 200 or response.status_code == 204:
        last_url = response.url
        return response.text
    elif response.status_code == 302:
        return response.headers['Location']
    else:
        try:
            response_dict = json.loads(response.text)
            if response.status_code == 408:
                error_string = "[" + response_dict['resCode'] + "] " + \
                    response_dict['resMsg']
            else:
                error_string = "[" + response_dict['errCode'] + "] " + \
                    response_dict['errMsg']
        except Exception:
            error_string = "[XXXX] Unidentified Error"

        log.debug("kia.postHTTP:Request failed, StatusCode: " +
                  str(response.status_code) + ', Error: ' + error_string)
        raise RuntimeError

    return ""


def getHTTPCookies(url: str = "") -> dict:
    try:
        session = requests.Session()
        response = session.get(url)
    except Exception:
        log.error("kia.getHTTPCookies: HTTP error", exc_info=True)
        raise

    if response.status_code == 200:
        cookies = session.cookies.get_dict()
    else:
        log.debug("kia.getHTTPCookies: Receiving cookies failed, StatusCode:" +
                  " " + str(response.status_code))
        raise RuntimeError

    return cookies

# ---------- token management ----------


def getUserHash(user_id: str, password: str) -> str:
    try:
        account = user_id + ':' + password
        hash = hashlib.md5(account.encode()).hexdigest()
    except Exception:
        log.error("kia.getUserHash: hash error", exc_info=True)
        raise

    return hash


def loadToken(user_id: str, password: str, vehicle: int) -> dict:
    try:
        token_file = str(RAMDISK_PATH) + "/soc_kia_vehicle" + \
            str(vehicle) + "_token"
        with open(token_file, 'r', encoding='utf-8') as f:
            token = json.loads(f.read())
    except Exception:
        log.debug("kia.loadToken: token file error: ", exc_info=True)
        token = {
            "userHash": ""
            }
        pass

    try:
        if token["userHash"] != getUserHash(user_id, password):
            log.debug("kia.loadToken: account data changed")
            token = {
                "userHash": "",
                "deviceId": "",
                "accessToken": "",
                "gcmVehicleId": "",
                "refreshToken": "",
                "gcmClientId": "",
                "tokenType": ""
                }
    except Exception:
        log.error("kia.loadToken: token error", exc_info=True)
        raise

    return token


def saveToken(user_id: str, password: str, vehicle: int, token: dict) -> None:
    try:
        token["userHash"] = getUserHash(user_id, password)
        token_file = str(RAMDISK_PATH) + "/soc_kia_vehicle" + \
            str(vehicle) + "_token"
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(token))
    except Exception:
        log.debug("kia.saveToken: token could not be saved", exc_info=True)
        raise

# ---------- authentication ----------


def getCookies(brand: str) -> dict:
    log.info("Kia/Hyundai: Create Login-session")

    try:
        url = getString("base_url", brand) + \
              '/api/v1/user/oauth2/authorize?' + \
              'response_type=code&state=test&client_id=' + \
              getString("client_id", brand) + '&redirect_uri=' + \
              getString("base_url", brand) + '/api/v1/user/oauth2/redirect'
        cookies = getHTTPCookies(url)

        url = getString("base_url", brand) + '/api/v1/user/session'
        getHTTP(url=url, cookies=cookies)

        url = getString("base_url", brand) + '/api/v1/user/language'
        headers = {'Content-type': 'application/json'}
        data = {"lang": "en"}
        response = postHTTP(url=url, data=data,
                            headers=headers, cookies=cookies)

        url = getString("base_url", brand) + '/api/v1/user/session'
        deleteHTTP(url=url, cookies=cookies)
    except Exception:
        log.debug("kia.getCookies: " + response, exc_info=True)
        raise

    return cookies


def getDeviceId(brand: str) -> dict:
    log.info("Kia/Hyundai: Requesting device ids")

    token = {}

    try:
        token["gcmClientId"] = str(uuid.uuid4())
        token["gcmVehicleId"] = str(uuid.uuid4())

        url = getString("base_url", brand) + \
            '/api/v1/spa/notifications/register'
        data = {
            "pushRegId": getString("gcm_sender_id", brand),
            "pushType": "GCM",
            "uuid": str(uuid.uuid4())
            }
        headers = {
            'Authorization': '',
            'Ccsp-Device-Id': '',
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'Offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Content-type': 'application/json; charset=UTF-8',
            'Content-Length': str(len(data)),
            'Host': getString("host", brand),
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = postHTTP(url=url, data=data, headers=headers)

        response_dict = json.loads(response)
        token["deviceId"] = response_dict['resMsg']['deviceId']

        log.debug("Kia/Hyundai: DeviceId = " + token["deviceId"][:8] + "[...]")
    except Exception:
        log.error("kia.getDeviceId: Request device id failed")
        log.debug("kia.getDeviceId: Request device id failed: " +
                  response, exc_info=True)
        raise

    log.info("Sending VersionInfo")
    try:
        url = getString("base_url", brand) + '/api/v1/spa/devices/version'

        data = {
            "teleType": 'none',
            "appVer": '2.1.9',
            "buildVer": '7.1.2',
            "phoneType": 'SM-G988N',
            "osType": 'android',
            "osVer": '7.1.2'
            }
        headers = {
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'Offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Content-type': 'application/json; charset=UTF-8',
            'Content-Length': str(len(data)),
            'Host': getString("host", brand),
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = postHTTP(url=url, data=data, headers=headers)
    except Exception:
        log.error("kia.getDeviceId: Set version info failed")
        log.debug("kia.getDeviceId: Set version info failed: " +
                  response, exc_info=True)
        raise

    token["userHash"] = ""
    token["tokenType"] = ""
    token["accessToken"] = ""
    token["refreshToken"] = ""

    return token


def getAuthCode(username: str, password: str, brand: str,
                cookies: dict) -> str:
    global last_cookies

    log.info("Kia/Hyundai: Sending username/password")

    try:
        url = getString("base_url", brand) + '/api/v1/user/integrationinfo'
        headers = {'Content-type': 'application/json'}
        response = getHTTP(url=url, headers=headers, cookies=cookies)

        response_dict = json.loads(response)
        user_id = response_dict['userId']
        service_id = response_dict['serviceId']
        log.debug("Kia/Hyundai: UserId = " + user_id[:8] + "[...]")
        log.debug("Kia/Hyundai: ServiceId = " + service_id[:8] + "[...]")

        url = 'https://eu-account.' + brand + '.com/auth/realms/eu' + brand + \
              'idm/protocol/openid-connect/auth?client_id=' + \
              getString("auth_client_id", brand) + \
              '&scope=openid%20profile%20email%20phone&response_type=code&' + \
              'hkid_session_reset=true&redirect_uri=' + \
              getString("base_url", brand) + '/api/v1/user/integration/' + \
              'redirect/login&ui_locales=en&state=' + \
              service_id + ':' + user_id
        headers = {}
        response = getHTTP(url=url, headers=headers, cookies=cookies)

        left = response.find('action="') + 8
        right = response.find('"', left)
        url = response[left:right].replace('&amp;', '&')
        data = urlparse.urlencode({'username': username, 'password': password,
                                   'credentialId': ''})
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 4.1.1; Galaxy Nexus ' +
                          'Build/JRO03C) AppleWebKit/535.19 (KHTML, ' +
                          'like Gecko) Chrome/18.0.1025.166 Mobile ' +
                          'Safari/535.19_CCS_APP_AOS'
            }
        cookies['AUTH_SESSION_ID'] = last_cookies['AUTH_SESSION_ID']
        response = postHTTP(url=url, data=data, headers=headers,
                            cookies=cookies, allow_redirects=False)

        url = response
        response = getHTTP(url=url, cookies=cookies, allow_redirects=True)

        url = getString("base_url", brand) + '/api/v1/user/silentsignin'
        headers = {'Content-type': 'text/plain;charset=UTF-8'}
        data = {'intUserId': ""}
        response = postHTTP(url=url, data=data, headers=headers,
                            cookies=cookies, allow_redirects=False)
        response_dict = json.loads(response)
        response_url = response_dict['redirectUrl']
        parsed = urlparse.urlparse(response_url)
        auth_code = ''.join(parse_qs(parsed.query)['code'])
    except Exception:
        log.error("kia.getAuthCode: Login failed")
        log.debug("kia.getAuthCode: Login failed: " + response, exc_info=True)
        raise

    log.debug("Kia/Hyundai: AuthCode = " + auth_code[:8] + "[...]")

    return auth_code


def getAuthToken(auth_code: str, token: dict, brand: str) -> dict:
    log.info("Kia/Hyundai: Requesting access token")

    try:
        url = getString("base_url", brand) + '/api/v1/user/oauth2/token'
        data = 'client_id=' + getString("client_id", brand) + \
               '&grant_type=authorization_code&code=' + \
               auth_code + '&redirect_uri=' + getString("base_url", brand) + \
               '%2Fapi%2Fv1%2Fuser%2Foauth2%2Fredirect'
        headers = {
            'Authorization': getString("basic_token", brand),
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'Offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Content-type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(data)),
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = postHTTP(url=url, headers=headers, data=data)

        access_token = json.loads(response)
        token["tokenType"] = access_token["token_type"]
        token["accessToken"] = access_token["access_token"]
        token["refreshToken"] = access_token["refresh_token"]

    except Exception:
        log.error("kia.getAuthToken: Login failed")
        log.debug("kia.getAuthToken: Login failed: " + response, exc_info=True)
        raise

    log.debug("Kia/Hyundai: AuthToken = " + token["accessToken"][:8] + "[...]")

    return token


def registerDevice(token: dict, brand: str) -> None:
    log.info("Kia/Hyundai: Registering DeviceId")

    try:
        url = getString("base_url", brand) + '/api/v1/spa/notifications/' + \
                        token["deviceId"] + '/register'
        data = {}
        headers = {
            'Authorization': token["tokenType"] + ' ' + token["accessToken"],
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'Offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Content-Length': '0',
            'Host': getString("host", brand),
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = postHTTP(url=url, data=data, headers=headers)
    except Exception:
        log.error("kia.getAuthToken: Login failed")
        log.debug("kia.getAuthToken: Login failed: " + response, exc_info=True)
        raise

    return


def requestToken(user_id: str, password: str, brand: str) -> dict:
    log.info("Kia/Hyundai: Token request starting")

    try:
        cookies = getCookies(brand)
        token = getDeviceId(brand)
        auth_code = getAuthCode(user_id, password, brand, cookies)
        token = getAuthToken(auth_code, token, brand)
        token["userHash"] = getUserHash(user_id, password)
        registerDevice(token, brand)
    except Exception:
        log.error("kia.requestToken: Login failed")
        log.debug("kia.requestToken: ", exc_info=True)
        raise

    return token


def refreshToken(token: dict, brand: str) -> dict:
    log.info("Kia/Hyundai: Token refresh starting")

    try:
        url = getString("base_url", brand) + '/api/v1/user/oauth2/token'
        data = 'client_id=' + getString("client_id", brand) + \
               '&grant_type=refresh_token&refresh_token=' + \
               token["refreshToken"] + \
               '&redirect_uri=' + getString("base_url", brand) + \
               '%2Fapi%2Fv1%2Fuser%2Foauth2%2Fredirect'
        headers = {
            'Authorization': getString("basic_token", brand),
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'Offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Content-type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(data)),
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }

        response = postHTTP(url=url, headers=headers, data=data)

        token_new = json.loads(response)
        token["tokenType"] = token_new["token_type"]
        token["accessToken"] = token_new["access_token"]

    except Exception:
        log.error("kia.refreshToken: refresh token failed")
        log.debug("kia.refreshToken: refresh token error: " +
                  response, exc_info=True)
        raise

    log.debug("kia.refreshToken: New access token = " +
              token["accessToken"][:8] + "...")

    return token


def getControlToken(pin: str, token: dict, brand: str) -> str:
    log.info("Kia/Hyundai: Sending PIN")

    try:
        url = getString("base_url", brand) + '/api/v1/user/pin'
        data = {"deviceId": token["deviceId"], "pin": pin}
        headers = {
            'Authorization': token["tokenType"] + ' ' + token["accessToken"],
            'Content-type': 'application/json;charset=UTF-8',
            'Content-Length': str(len(data)),
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12'
            }
        response = putHTTP(url=url, data=data, headers=headers)

        response_dict = json.loads(response)
        control_token = 'Bearer ' + response_dict['controlToken']
    except Exception:
        log.error("kia.getControlToken: Sending PIN failed")
        log.debug("kia.getControlToken: Sending PIN error: " +
                  response, exc_info=True)
        raise

    log.debug("kia.refreshToken: control token = " +
              control_token[7:15] + "...")

    return control_token

# ---------- API functions ----------


def getVehicleId(vin: str, token: dict, brand: str) -> str:
    log.info("Kia/Hyundai: Requesting vehicle list")

    try:
        url = getString("base_url", brand) + '/api/v1/spa/vehicles'
        headers = {
            'Authorization': token["tokenType"] + ' ' + token["accessToken"],
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = getHTTP(url=url, headers=headers)

        vehicle_id = ""
        response_dict = json.loads(response)
        for vehicle in response_dict['resMsg']['vehicles']:
            if vehicle['vin'] == vin:
                vehicle_id = vehicle['vehicleId']
                vehicle_name = vehicle['nickname']

        if vehicle_id == "":
            log.error("Kia/Hyundai: VIN " + vin + " unknown")
            raise

    except Exception:
        log.error("kia.getVehicleId: failed")
        log.debug("kia.getVehicleId: error: " + response, exc_info=True)
        raise

    log.debug("kia.getVehicleId: VehicleId = " + vehicle_id[:8] +
              "... (" + vehicle_name + ")")

    return vehicle_id


def doPrewakeup(vehicle_id: str, token: dict, brand: str) -> None:
    log.info("Kia/Hyundai: Triggering Pre-Wakeup")

    try:
        url = getString("base_url", brand) + '/api/v1/spa/vehicles/' +\
              vehicle_id + '/control/engine'
        data = {"action": "prewakeup", "deviceId": token["deviceId"]}
        headers = {
            'Authorization': token["tokenType"] + ' ' + token["accessToken"],
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'offset': '2',
            'Content-Type': 'application/json; charset=UTF-8',
            'Content-Length': str(len(data)),
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = postHTTP(url=url, data=data, headers=headers, timeout=125)
    except Exception:
        log.error("kia.doPrewakeup: failed")
        log.debug("kia.doPrewakeup: error: " + response, exc_info=True)
        raise

    return


def getStatusFull(vehicle_id: str, control_token: str,
                  token: dict, brand: str) -> CarState:
    log.info("Kia/Hyundai: Triggering Update")

    try:
        url = getString("base_url", brand) + '/api/v2/spa/vehicles/' + \
              vehicle_id + '/ccs2/carstatus'
        headers = {
            'Authorization': control_token,
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'offset': '2',
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = getHTTP(url=url, headers=headers, timeout=125)
    except Exception:
        log.error("kia.getStatusFull: triggering update failed")
        log.debug("kia.getStatusFull: triggering update error: " +
                  response, exc_info=True)
        raise

    log.info("Kia/Hyundai: Waiting 130 seconds")
    time.sleep(130)

    log.info("Kia/Hyundai: Receiving status")

    try:
        url = getString("base_url", brand) + '/api/v1/spa/vehicles/' + \
              vehicle_id + '/ccs2/carstatus/latest'
        headers = {
            'Authorization': token["tokenType"] + ' ' + token["accessToken"],
            'Ccsp-Device-Id': token["deviceId"],
            'Ccsp-Service-Id': getString("client_id", brand),
            'Ccsp-Application-Id': getString("app_id", brand),
            'Clientid': token["gcmClientId"],
            'Vehicleid': token["gcmVehicleId"],
            'Ccuccs2protocolsupport': '0',
            'Offset': '2',
            'Host': getString("host", brand),
            'Connection': 'close',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'okhttp/3.12.12',
            'Stamp': getStamp(brand)
            }
        response = getHTTP(url=url, headers=headers)
        response_dict = json.loads(response)

        soc = int(response_dict['resMsg']['state']['Vehicle']['Green']
                               ['BatteryManagement']['BatteryRemain']['Ratio'])
        range = float(response_dict['resMsg']['state']['Vehicle']['Drivetrain']
                                   ['FuelSystem']['DTE']['Total'])

    except Exception:
        log.error("kia.getStatusFull: receiving update failed")
        log.debug("kia.getStatusFull: receiving update error: " +
                  response, exc_info=True)
        raise

    return CarState(soc, range)

# ---------- main function ----------


def fetch_soc(user_id: str, password: str, pin: str,
              vin: str, vehicle: int) -> CarState:

    log.info("Kia/Hyundai: Update starting")

    try:
        brand = getBrand(vin)
        token = loadToken(user_id, password, vehicle)
        if token["accessToken"] == "":
            token = requestToken(user_id, password, brand)
        else:
            token = refreshToken(token, brand)
        saveToken(user_id, password, vehicle, token)
    except Exception:
        log.error("kia.fetch_soc: login error, vehicle: " + str(vehicle))
        log.debug("kia.fetch_soc: ", exc_info=True)
        raise

    try:
        vehicle_id = getVehicleId(vin, token, brand)
        doPrewakeup(vehicle_id, token, brand)
        control_token = getControlToken(pin, token, brand)
        soc_state = getStatusFull(vehicle_id, control_token, token, brand)
    except Exception:
        log.error("kia.fetch_soc: API error, vehicle: " + str(vehicle))
        log.debug("kia.fetch_soc: ", exc_info=True)
        raise

    return soc_state
