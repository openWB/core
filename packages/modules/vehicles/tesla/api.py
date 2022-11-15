#!/usr/bin/python3

import logging
import time
import json
from typing import Tuple

from modules.common import req
from modules.common.fault_state import FaultState
from modules.vehicles.tesla.config import TeslaSocToken

log = logging.getLogger("soc."+__name__)

# UA = "Mozilla/5.0 (Linux; Android 10; Pixel 3 Build/QQ2A.200305.002; wv) AppleWebKit/537.36 (KHTML, like Gecko)
# Version/4.0 Chrome/85.0.4183.81 Mobile Safari/537.36"
# X_TESLA_USER_AGENT = "TeslaApp/3.10.9-433/adff2e065/android/10"

# The documentation here:
#   https://tesla-api.timdorr.com/api-basics/authentication Says:
# "Avoid setting a User-Agent header that looks like a browser (such
#  as Chrome or Safari). The SSO service has protections in place
#  that will require executing JavaScript if a browser-like user
#  agent is detected."
# So to get a token I set the strings to:
UA = ""
X_TESLA_USER_AGENT = ""


def post_wake_up_command(vehicle: int, token: TeslaSocToken) -> str:
    vehicle_id = __get_vehicle_id(vehicle, token)
    command = "vehicles/"+str(vehicle_id)+"/wake_up"
    log.debug("Sending command: \"%s\"" % (command))
    headers = {
        "user-agent": UA,
        "x-tesla-user-agent": X_TESLA_USER_AGENT,
        "authorization": "bearer " + token.access_token
    }
    session = req.get_http_session()
    response = session.post("https://owner-api.teslamotors.com/api/1/" + command, headers=headers, timeout=50).json()
    return response["response"]["state"]


def request_soc_range(vehicle: int, token: TeslaSocToken) -> Tuple[float, float]:
    vehicle_id = __get_vehicle_id(vehicle, token)
    data_part = "vehicles/"+str(vehicle_id)+"/vehicle_data"
    response = __request_data(data_part, token)
    response = json.loads(response)
    soc = response["response"]["charge_state"]["battery_level"]
    # convert miles to km
    range = float(response["response"]["charge_state"]["battery_range"]) * 1.60934
    return float(soc), range


def validate_token(token: TeslaSocToken) -> TeslaSocToken:
    expiration = token.created_at + token.expires_in
    log.debug("No need to authenticate. Valid token already present.")
    if time.time() > expiration:
        log.debug("Access token expired. Refreshing token.")
        token = __refresh_token(token)
    return token


def __refresh_token(token: TeslaSocToken) -> TeslaSocToken:
    headers = {"user-agent": UA, "x-tesla-user-agent": X_TESLA_USER_AGENT}
    payload = {
        "grant_type": "refresh_token",
        "client_id": "ownerapi",
        "refresh_token": token.refresh_token,
        "scope": "openid email offline_access",
    }
    resp = req.get_http_session().post("https://auth.tesla.com/oauth2/v3/token",
                                       headers=headers,
                                       json=payload,
                                       timeout=50)
    log.debug("received refresh token")
    resp_json = resp.json()
    token.refresh_token = resp_json["refresh_token"]
    token.access_token = resp_json["access_token"]
    token.created_at = time.time()
    token.expires_in = resp_json["expires_in"]
    log.debug("Token Refresh succeeded")
    return token


def __get_vehicle_id(index: int, token: TeslaSocToken) -> str:
    vehicles = __request_data('vehicles', token)
    try:
        vehicle_id = str(json.loads(vehicles)["response"][index]["id"])
        log.debug("vehicle_id for entry %d: %s" % (index, vehicle_id))
    except IndexError:
        raise FaultState.error("Zur Tesla-ID "+str(index)+" konnte kein Fahrzeug im Account gefunden werden.")
    return vehicle_id


def __request_data(data_part: str, token: TeslaSocToken) -> str:
    log.debug("Requesting data: \"%s\"" % (data_part))
    headers = {
        "user-agent": UA,
        "x-tesla-user-agent": X_TESLA_USER_AGENT,
        "authorization": "bearer " + token.access_token
    }
    response = req.get_http_session().get("https://owner-api.teslamotors.com/api/1/" + data_part,
                                          headers=headers,
                                          timeout=50)
    return response.text
