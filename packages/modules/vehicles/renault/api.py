#!/usr/bin/env python3

import json
import urllib
import logging
from modules.common.component_state import CarState
from modules.common import req
from modules.vehicles.renault.config import RenaultConfiguration

log = logging.getLogger(__name__)

GIGYA_ROOTURL = 'https://accounts.eu1.gigya.com'
GIGYA_API = '3_7PLksOyBRkHv126x5WhHb-5pqC1qFR8pQjxSeLB6nhAnPERTUlwnYoznHSxwX668'
KAMEREON_ROOTURL = 'https://api-wired-prod-1-euw1.wrd-aws.com'
KAMEREON_API_KEY = 'VAX7XYKGfa92yMvXculCkEFyfZbuM7Ss'


def fetch_soc(config: RenaultConfiguration) -> CarState:
    country_data = {'country': config.country}
    # Step 1- skipped
    # Step 2
    payload = {'loginID': config.user_id, 'password': config. password, 'apiKey': GIGYA_API}
    gigya_session = req.get_http_session().post(f"{GIGYA_ROOTURL}/accounts.login", data=payload).json()

    # Step 3
    gigyacookievalue = gigya_session['sessionInfo']['cookieValue']
    payload = {'login_token': gigyacookievalue, 'apiKey': GIGYA_API}
    gigya_account = req.get_http_session().post(f"{GIGYA_ROOTURL}/accounts.getAccountInfo", data=payload).json()

    # Step 4
    payload = {'login_token': gigyacookievalue, 'apiKey': GIGYA_API,
               'fields': 'data.personId,data.gigyaDataCenter', 'expiration': 900}
    gigya_jwt = req.get_http_session().post(f"{GIGYA_ROOTURL}/accounts.getJWT", data=payload).json()

    # Step 5
    gigya_jwttoken = gigya_jwt['id_token']
    kamereonpersonid = gigya_account['data']['personId']
    kamereon_per = req.get_http_session().get(f"{KAMEREON_ROOTURL}/commerce/v1/persons/{kamereonpersonid}",
                                              headers={'x-gigya-id_token': gigya_jwttoken, 'apikey': KAMEREON_API_KEY},
                                              data=country_data).json()

    # Step 6 - skipped
    # Step 7 - vehicles
    kamereonaccountid = kamereon_per['accounts'][0]['accountId']
    log.debug(f"account id {kamereonaccountid}")
    # vehic = req.get_http_session().get(f"{KAMEREON_ROOTURL}/commerce/v1/accounts/{kamereonaccountid}/vehicles",
    #                                    headers={'x-gigya-id_token': gigya_jwttoken, 'apikey': KAMEREON_API_KEY},
    #                                    data=country_data).json()
    # wirft requests.exceptions.HTTPError: 400 Client Error: Bad Request for url

    data = urllib.parse.urlencode(country_data)
    data = data.encode('Big5')
    reg = urllib.request.Request(KAMEREON_ROOTURL + '/commerce/v1/accounts/' +
                                 kamereonaccountid + '/vehicles?' + data.decode("utf-8"))
    reg.add_header('x-gigya-id_token', gigya_jwttoken)
    reg.add_header('apikey', KAMEREON_API_KEY)
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    vehic = json.loads(responsetext)

    if config.vin is None or len(config.vin) < 10:
        vin = vehic['vehicleLinks'][0]['vin']
    else:
        vin = config.vin

    # Step 8 - battery-status
    # batt = req.get_http_session().get(f"{KAMEREON_ROOTURL}/commerce/v1/accounts/{kamereonaccountid}/kamereon/kca/"
    #                                   f"car-adapter/v2/cars/{vin}/battery-status",
    #                                   headers={'x-gigya-id_token': gigya_jwttoken, 'apikey': KAMEREON_API_KEY},
    #                                   data=country_data).json()
    # wirft requests.exceptions.HTTPError: 400 Client Error: Bad Request for url:

    data = urllib.parse.urlencode(country_data)
    data = data.encode('Big5')
    reg = urllib.request.Request(KAMEREON_ROOTURL + '/commerce/v1/accounts/' +
                                 kamereonaccountid + '/kamereon/kca/car-adapter/v2/cars/'
                                 + vin + '/battery-status?' + data.decode("utf-8"))
    reg.add_header('x-gigya-id_token', gigya_jwttoken)
    reg.add_header('apikey', KAMEREON_API_KEY)
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    batt = json.loads(responsetext)

    return CarState(soc=float(batt['data']['attributes']['batteryLevel']),
                    range=float(batt['data']['attributes']['batteryAutonomy']))
