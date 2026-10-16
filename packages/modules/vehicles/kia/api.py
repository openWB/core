#!/usr/bin/env python3

import base64
from datetime import datetime
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
try:
    from helpermodules.constants import RAMDISK_PATH
except ImportError:
    # Older/variant openWB installs don't export RAMDISK_PATH from
    # helpermodules.constants. Fall back to the standard location that
    # openWB uses internally: <openWB-root>/ramdisk. This file lives at
    # <root>/packages/modules/vehicles/kia/api.py -> parents[4] == <root>.
    from pathlib import Path
    RAMDISK_PATH = Path(__file__).resolve().parents[4] / "ramdisk"

log = logging.getLogger(__name__)


# ---------- password encryption (IDPConnect login) ----------


def rsaEncryptPassword(n_b64url: str, e_b64url: str, password: str) -> str:
    """RSA/PKCS#1 v1.5 encrypt the plaintext password.

    The IDPConnect '/auth/api/v1/accounts/certs' endpoint returns the public
    key as a JWK (base64url-encoded modulus 'n' and exponent 'e', no padding).
    Prefers 'cryptography' (usually already present via requests); falls back
    to 'pycryptodome' if only that is installed.
    Returns the ciphertext as a lowercase hex string.
    """
    n_bytes = base64.urlsafe_b64decode(n_b64url + "==")
    e_bytes = base64.urlsafe_b64decode(e_b64url + "==")
    n = int.from_bytes(n_bytes, "big")
    e = int.from_bytes(e_bytes, "big")
    try:
        from cryptography.hazmat.primitives.asymmetric.rsa import \
            RSAPublicNumbers
        from cryptography.hazmat.primitives.asymmetric import padding
        pub = RSAPublicNumbers(e, n).public_key()
        encrypted = pub.encrypt(password.encode("utf-8"), padding.PKCS1v15())
    except ImportError:
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        key = RSA.construct((n, e))
        cipher = PKCS1_v1_5.new(key)
        encrypted = cipher.encrypt(password.encode("utf-8"))
    return encrypted.hex()


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
        elif param_id == "login_form_host":
            paramStr = "https://idpconnect-eu.kia.com"
        elif param_id == "client_secret":
            paramStr = "secret"
        elif param_id == "redirect_uri":
            paramStr = getString("base_url", brand) + \
                       "/api/v1/user/oauth2/redirect"
        elif param_id == "oneapp_client_id":
            paramStr = "01b36c86-79e8-486c-8009-15f2ad88d670"
        elif param_id == "oneapp_redirect_uri":
            paramStr = "https://oneapp.kia.com/redirect"
        elif param_id == "cci_api_url":
            paramStr = "https://cci-api-eu.kia.com"
        elif param_id == "cci_package_id":
            paramStr = "com.kia.oneapp.eu"
        elif param_id == "cci_client_name":
            paramStr = "kia"
        elif param_id == "cci_client_os_version":
            paramStr = "27"
        elif param_id == "cci_notification_provider":
            paramStr = "IOS_APPSTORE"
        else:
            raise RuntimeError

    if brand == 'hyundai':
        if param_id == "app_id":
            paramStr = "014d2225-8495-4735-812d-2616334fd15d"
        elif param_id == "client_id":
            paramStr = "6d477c38-3ca4-4cf3-9557-2a1929a94654"
        elif param_id == "auth_client_id":
            paramStr = "64621b96-0f0d-11ec-82a8-0242ac130003"
        elif param_id == "gcm_sender_id":
            paramStr = "dQtCqr7gRjy31Ao4nPiLVy:APA91bF_tv9yPOTFa-sW9-vCxO" + \
                       "VpzD_iLjRopN_zaKgPKdwS7OYTWFN626-ObhZyzka5kYFKG0K" + \
                       "fCsuMOUD5aw9Gyrdh-IeBQZHIcfb5YNUrQBvfqQxbggk9kO6g" + \
                       "ZeFbCpCLHZB6wITC"
        elif param_id == "basic_token":
            paramStr = "Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk" + \
                       "0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5" + \
                       "aVFobUlGampvWTRJcHhzVg=="
        elif param_id == "stamp_pad":
            paramStr = "445B6846AFEF0D726646776865A650C9F3A8B7B3AB22A1951" + \
                       "63F7A898D962F7CB21F967FA54BE5521AA60B10F6B7E0FADC3B"
        elif param_id == "host":
            paramStr = "prd.eu-ccapi.hyundai.com:8080"
        elif param_id == "base_url":
            paramStr = "https://prd.eu-ccapi.hyundai.com:8080"
        elif param_id == "login_form_host":
            paramStr = "https://idpconnect-eu.hyundai.com"
        elif param_id == "client_secret":
            paramStr = "KUy49XxPzLpLuoK0xhBC77W6VXhmtQR9iQhmIFjjoY4IpxsV"
        elif param_id == "redirect_uri":
            paramStr = getString("base_url", brand) + \
                       "/api/v1/user/oauth2/token"
        elif param_id == "oneapp_client_id":
            paramStr = "4f4953b5-02e1-4dbc-8599-87e983ee1be5"
        elif param_id == "oneapp_redirect_uri":
            paramStr = "https://oneapp.hyundai.com/redirect"
        elif param_id == "cci_api_url":
            paramStr = "https://cci-api-eu.hyundai.com"
        elif param_id == "cci_package_id":
            paramStr = "com.hyundai.oneapp.eu"
        elif param_id == "cci_client_name":
            paramStr = "hyundai"
        elif param_id == "cci_client_os_version":
            paramStr = "18.7"
        elif param_id == "cci_notification_provider":
            paramStr = "APNS"
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
        log.exception("kia.getBrand: VIN error")
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
        log.exception("kia.getStamp: stamp error")
        raise

    return stamp

# ---------- HTTP functions ----------


last_cookies = {}
last_url = ""


def getHTTP(url: str = "", headers: str = "", cookies: str = "",
            timeout: int = 30, allow_redirects: bool = True) -> str:
    global last_cookies

    try:
        response = requests.get(url, headers=headers,
                                cookies=cookies, timeout=timeout,
                                allow_redirects=allow_redirects)
    except Exception:
        log.exception("kia.getHTTP: HTTP error")
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
            log.exception("kia.getHTTP:Request failed")

        log.error("kia.getHTTP:Request failed, StatusCode: " +
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
        log.exception("kia.putHTTP: HTTP error")
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
            log.exception("kia.putHTTP:Request failed")

        log.error("kia.putHTTP:Request failed, StatusCode: " +
                  str(response.status_code) + ', Error: ' + error_string)
        raise RuntimeError

    return ""


def deleteHTTP(url: str = "", headers: str = "", cookies: str = "",
               timeout: int = 30) -> None:
    try:
        response = requests.delete(url, headers=headers, cookies=cookies,
                                   timeout=timeout)
    except Exception:
        log.exception("kia.deleteHTTP: HTTP error: " + response)
        raise

    return


def postHTTP(url: str = "", data: Union[str, dict] = "",
             headers: str = "", cookies: str = "", timeout: int = 30,
             allow_redirects: bool = True) -> str:
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
        log.exception("kia.postHTTP: HTTP error")
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
            log.exception("kia.postHTTP:Request failed")

        log.error("kia.postHTTP:Request failed, StatusCode: " +
                  str(response.status_code) + ', Error: ' + error_string)
        raise RuntimeError("kia.postHTTP StatusCode " +
                           str(response.status_code) + " " + error_string)

    return ""


def getHTTPCookies(url: str = "") -> dict:
    try:
        session = requests.Session()
        response = session.get(url)
    except Exception:
        log.exception("kia.getHTTPCookies: HTTP error")
        raise

    if response.status_code == 200:
        cookies = session.cookies.get_dict()
    else:
        log.error("kia.getHTTPCookies: Receiving cookies failed, StatusCode:" +
                  " " + str(response.status_code))
        raise RuntimeError

    return cookies

# ---------- token management ----------


def getUserHash(user_id: str, password: str) -> str:
    try:
        account = user_id + ':' + password
        hash = hashlib.md5(account.encode()).hexdigest()
    except Exception:
        log.exception("kia.getUserHash: hash error")
        raise

    return hash


def loadToken(user_id: str, password: str, vehicle: int) -> dict:
    try:
        token_file = str(RAMDISK_PATH) + "/soc_kia_vehicle" + \
            str(vehicle) + "_token"
        with open(token_file, 'r', encoding='utf-8') as f:
            token = json.loads(f.read())
    except Exception:
        log.exception("kia.loadToken: token file error: ")
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
                "tokenType": "",
                "cciAccessToken": "",
                "cciRefreshToken": "",
                "nonCcsToken": "",
                "nonCcsRefreshToken": "",
                "exchangeableAccessToken": "",
                "exchangeableRefreshToken": "",
                "idToken": "",
            }
    except Exception:
        log.exception("kia.loadToken: token error")
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
        log.exception("kia.saveToken: token could not be saved")
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
        log.exception("kia.getCookies: " + response)
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
        log.exception("kia.getDeviceId: Request device id failed: " +
                      response)
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
        log.exception("kia.getDeviceId: Set version info failed: " +
                      response)
        raise

    token["userHash"] = ""
    token["tokenType"] = ""
    token["accessToken"] = ""
    token["refreshToken"] = ""

    return token


def getAuthCode(username: str, password: str, brand: str,
                cookies: dict) -> str:
    log.info("Kia/Hyundai: Sending username/password (OneApp/CCI flow)")

    # Die alte IDPConnect-Anmeldung über den "legacy" client_id wird von
    # Kia/Hyundais WAF inzwischen serverseitig als "abusing request" blockiert
    # (betrifft alle Nutzer dieses client_id, kein individuelles Account-
    # Problem). Der OneApp-client_id umgeht das, siehe hyundai_kia_connect_api
    # Issue #1273. Der resultierende Auth-Code wird anschließend über
    # exchangeCciToken()/exchangeCcsToken() in einen auf den bestehenden
    # ccapi:8080-Endpunkten gültigen Token getauscht.
    host = getString("login_form_host", brand)
    client_id = getString("oneapp_client_id", brand)
    redirect_uri = getString("oneapp_redirect_uri", brand)

    # The '_CCS_APP_AOS' suffix is REQUIRED — without it the authorize
    # endpoint answers "400 Bad Request".
    mobile_ua = ('Mozilla/5.0 (Linux; Android 4.1.1; Galaxy Nexus '
                 'Build/JRO03C) AppleWebKit/535.19 (KHTML, like Gecko) '
                 'Chrome/18.0.1025.166 Mobile Safari/535.19_CCS_APP_AOS')

    session = requests.Session()
    session.headers.update({'User-Agent': mobile_ua})

    response = ""
    try:
        # Step 1: load the authorize page to obtain session cookies
        auth_url = (host + '/auth/api/v2/user/oauth2/authorize'
                    '?response_type=code&client_id=' + client_id +
                    '&redirect_uri=' + urlparse.quote(redirect_uri, safe='') +
                    '&lang=en&state=ccsp&country=de')
        auth_resp = session.get(auth_url, timeout=30, allow_redirects=True)
        if ('abusing' in auth_resp.text.lower() or
                '/error?status=400' in auth_resp.url):
            log.error("kia.getAuthCode: WAF hat die Anmeldung blockiert "
                      "('abusing request') - kein Account-Problem")
            raise RuntimeError

        # Step 2: fetch the RSA public key (JWK) for password encryption
        certs = session.get(host + '/auth/api/v1/accounts/certs', timeout=30)
        if certs.status_code != 200:
            log.error("kia.getAuthCode: RSA certs fetch failed, StatusCode: " +
                      str(certs.status_code))
            raise RuntimeError
        jwk = certs.json().get('retValue', {})
        kid = jwk.get('kid', '')
        encrypted_pw = rsaEncryptPassword(jwk['n'], jwk['e'], password)

        # Step 3: POST the sign-in form with the encrypted password
        data = {
            'client_id': client_id,
            'encryptedPassword': 'true',
            'password': encrypted_pw,
            'redirect_uri': redirect_uri,
            'scope': '',
            'nonce': '',
            'state': 'ccsp',
            'username': username,
            'connector_session_key': '',
            'kid': kid,
            '_csrf': '',
        }
        signin = session.post(host + '/auth/account/signin', data=data,
                              timeout=30, allow_redirects=False)
        if signin.status_code != 302:
            log.error("kia.getAuthCode: Signin failed, StatusCode: " +
                      str(signin.status_code) + " - check username/password")
            raise RuntimeError

        location = signin.headers.get('Location', '')
        code_list = parse_qs(urlparse.urlparse(location).query).get('code')
        if not code_list:
            if '/web/v1/user/authorization' in location:
                log.error("kia.getAuthCode: Account consent required - log in "
                          "once via browser to accept the terms")
            else:
                log.error("kia.getAuthCode: No auth code in redirect: " +
                          location[:250])
            raise RuntimeError
        auth_code = code_list[0]

    except RuntimeError:
        raise
    except Exception:
        log.exception("kia.getAuthCode: Login failed: " + str(response))
        raise

    log.debug("Kia/Hyundai: AuthCode = " + auth_code[:8] + "[...]")

    return auth_code

# ---------- OneApp/CCI token exchange ----------


def getCciHeaders(brand: str, device_id: str, cci_access_token: str = "",
                  non_ccs_token: str = "", exchangeable_token: str = "",
                  content_type: str = "") -> dict:
    offset = datetime.now().astimezone().strftime("%z")  # e.g. +0200
    headers = {
        'client-id': getString("cci_package_id", brand),
        'client-name': getString("cci_client_name", brand),
        'client-version': '1.3.3',
        'client-os-code': 'ios',
        'client-os-version': getString("cci_client_os_version", brand),
        'client-device-id': device_id,
        'client-device-model': 'iPhone',
        'client-notification-provider-type': getString("cci_notification_provider", brand),
        'locale': 'DE',
        'Accept': 'application/json',
        'Accept-Language': 'de',
        'User-Agent': 'okhttp/3.12.12',
        'timezone': (offset[:3] + ':' + offset[3:]) if offset else '+00:00',
    }
    if non_ccs_token:
        headers['Authentication'] = non_ccs_token
    if cci_access_token:
        headers['authorization'] = 'Bearer ' + cci_access_token.removeprefix('Bearer ').strip()
    if exchangeable_token:
        headers['exchangeable-token'] = exchangeable_token
        headers['non-ccs-token'] = non_ccs_token
    if content_type:
        headers['Content-Type'] = content_type
    else:
        headers['Content-Length'] = '0'
    return headers


def exchangeCciToken(auth_code: str, device_id: str, brand: str) -> dict:
    log.info("Kia/Hyundai: Exchanging OneApp auth code for CCI token")

    cci_domain_api_url = getString("cci_api_url", brand) + '/domain/api/'
    headers = getCciHeaders(brand, device_id)
    response = requests.post(cci_domain_api_url + 'v1/auth/token',
                             params={'code': auth_code}, headers=headers,
                             timeout=30)
    if response.status_code != 200:
        log.error("kia.exchangeCciToken: CCI-Token-Austausch fehlgeschlagen, StatusCode: " +
                  str(response.status_code) + ': ' + response.text[:200])
        raise RuntimeError
    cci = response.json()
    return {
        'cciAccessToken': cci.get('accessToken', ''),
        'cciRefreshToken': cci.get('refreshToken', ''),
        'nonCcsToken': cci.get('nonCcsToken', ''),
        'exchangeableAccessToken': cci.get('exchangeableAccessToken', ''),
        'exchangeableRefreshToken': cci.get('exchangeableRefreshToken', ''),
        'nonCcsRefreshToken': cci.get('nonCcsRefreshToken', ''),
        'idToken': cci.get('idToken', ''),
    }


def exchangeCcsToken(device_id: str, cci_access_token: str, non_ccs_token: str,
                     exchangeable_token: str, brand: str) -> str:
    log.info("Kia/Hyundai: Exchanging CCI token for CCS token")

    cci_domain_api_url = getString("cci_api_url", brand) + '/domain/api/'
    headers = getCciHeaders(brand, device_id, cci_access_token=cci_access_token,
                            non_ccs_token=non_ccs_token,
                            exchangeable_token=exchangeable_token)
    response = requests.post(cci_domain_api_url + 'v1/auth/token-exchange',
                             params={'serviceType': 'CCS'}, headers=headers,
                             timeout=30)
    if response.status_code != 200:
        log.error("kia.exchangeCcsToken: CCS-Token-Austausch fehlgeschlagen, StatusCode: " +
                  str(response.status_code) + ': ' + response.text[:200])
        raise RuntimeError
    data = response.json()
    ccs_token = data.get('accessToken') or data.get('ccsAccessToken') or ''
    if not ccs_token:
        log.error("kia.exchangeCcsToken: kein accessToken in Antwort: " + response.text[:200])
        raise RuntimeError
    return ccs_token


def refreshCciToken(token: dict, brand: str) -> dict:
    log.info("Kia/Hyundai: CCI token refresh starting")

    device_id = token.get('deviceId', '')
    cci_domain_api_url = getString("cci_api_url", brand) + '/domain/api/'
    headers = getCciHeaders(brand, device_id,
                            cci_access_token=token.get('cciAccessToken', ''),
                            non_ccs_token=token.get('nonCcsToken', ''),
                            exchangeable_token=token.get('exchangeableAccessToken', ''),
                            content_type='application/json')
    body = {
        'accessToken': token.get('cciAccessToken', '').removeprefix('Bearer '),
        'refreshToken': token.get('cciRefreshToken', ''),
        'exchangeableAccessToken': token.get('exchangeableAccessToken', ''),
        'exchangeableRefreshToken': token.get('exchangeableRefreshToken', ''),
        'nonCcsToken': token.get('nonCcsToken', ''),
        'nonCcsRefreshToken': token.get('nonCcsRefreshToken', ''),
        'idToken': token.get('idToken', ''),
    }
    response = requests.post(cci_domain_api_url + 'v2/auth/token-refresh',
                             json=body, headers=headers, timeout=30)
    if response.status_code != 200:
        log.error("kia.refreshCciToken: CCI-Token-Refresh fehlgeschlagen, StatusCode: " +
                  str(response.status_code) + ': ' + response.text[:200])
        raise RuntimeError
    data = response.json()
    token['cciAccessToken'] = data.get('accessToken', token.get('cciAccessToken', ''))
    token['cciRefreshToken'] = data.get('refreshToken', token.get('cciRefreshToken', ''))
    token['nonCcsToken'] = data.get('nonCcsToken', token.get('nonCcsToken', ''))
    token['exchangeableAccessToken'] = data.get(
        'exchangeableAccessToken', token.get('exchangeableAccessToken', ''))
    token['exchangeableRefreshToken'] = data.get(
        'exchangeableRefreshToken', token.get('exchangeableRefreshToken', ''))
    token['nonCcsRefreshToken'] = data.get('nonCcsRefreshToken', token.get('nonCcsRefreshToken', ''))
    token['idToken'] = data.get('idToken', token.get('idToken', ''))

    ccs_token = exchangeCcsToken(device_id, token['cciAccessToken'], token['nonCcsToken'],
                                 token['exchangeableAccessToken'], brand)
    token['tokenType'] = 'Bearer'
    token['accessToken'] = ccs_token
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
        log.exception("kia.getAuthToken: Login failed: " + response)
        raise

    return


def requestToken(user_id: str, password: str, brand: str) -> dict:
    log.info("Kia/Hyundai: Token request starting")

    try:
        # getCookies() is no longer needed: die OneApp/CCI getAuthCode()
        # erstellt ihre eigene Session. Legacy IDPConnect-Login (client_id,
        # getAuthToken) wird von Kia/Hyundais WAF blockiert (siehe #3410) -
        # stattdessen OneApp-Auth-Code über CCI gegen einen CCS-Token tauschen,
        # der von den bestehenden ccapi:8080-Endpunkten akzeptiert wird.
        token = getDeviceId(brand)
        auth_code = getAuthCode(user_id, password, brand, {})
        token.update(exchangeCciToken(auth_code, token["deviceId"], brand))
        token["accessToken"] = exchangeCcsToken(
            token["deviceId"], token["cciAccessToken"], token["nonCcsToken"],
            token["exchangeableAccessToken"], brand)
        token["tokenType"] = "Bearer"
        token["refreshToken"] = token["cciRefreshToken"]
        token["userHash"] = getUserHash(user_id, password)
        registerDevice(token, brand)
    except Exception:
        log.exception("kia.requestToken: ")
        raise

    return token


def refreshToken(token: dict, brand: str) -> dict:
    # Legacy IDPConnect-Refresh (client_id-basiert) ist vom selben WAF-Block
    # betroffen wie der Login - CCI-Refresh ist der einzig noch funktionierende Weg
    return refreshCciToken(token, brand)


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
        log.exception("kia.getControlToken: Sending PIN error: " +
                      response)
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
        log.exception("kia.getVehicleId: error: " + response)
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
        log.exception("kia.doPrewakeup: error: " + response)
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
        log.exception("kia.getStatusFull: triggering update error: " +
                      response)
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

        odometer = None
        try:
            odometer = float(response_dict['resMsg']['state']['Vehicle']
                                          ['Drivetrain']['Odometer'])
        except (KeyError, TypeError, ValueError):
            log.warning("kia.getStatusFull: odometer not available in "
                        "vehicle status response")

        warning = None
        try:
            target_soc = int(response_dict['resMsg']['state']['Vehicle']['Green']
                                          ['ChargingInformation']['TargetSoC']['Standard'])
            if target_soc < 100:
                warning = f"Das Fahrzeug begrenzt die Ladung selbst auf {target_soc}% (AC-Ladeziel)."
        except (KeyError, TypeError, ValueError):
            log.debug("kia.getStatusFull: AC-Ladeziel not available in vehicle status response")

    except Exception:
        log.exception("kia.getStatusFull: receiving update error: " +
                      response)
        raise

    return CarState(soc=soc, range=range, odometer=odometer, warning=warning)

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
            try:
                token = refreshToken(token, brand)
            except Exception:
                # Refresh can fail once the refresh token has expired or been
                # rotated server-side. Mirror hyundai_kia_connect_api: fall
                # back to a full login instead of leaving the module stuck.
                log.warning("kia.fetch_soc: token refresh failed, "
                            "falling back to full login")
                token = requestToken(user_id, password, brand)
        saveToken(user_id, password, vehicle, token)
    except Exception:
        log.exception("kia.fetch_soc: ")
        raise

    try:
        vehicle_id = getVehicleId(vin, token, brand)
        doPrewakeup(vehicle_id, token, brand)
        control_token = getControlToken(pin, token, brand)
        soc_state = getStatusFull(vehicle_id, control_token, token, brand)
    except Exception:
        log.exception("kia.fetch_soc: ")
        raise

    return soc_state
