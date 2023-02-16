#!/usr/bin/python3

import requests
import json
import time
import logging
from requests.exceptions import Timeout, RequestException
from json import JSONDecodeError
from typing import Tuple
from modules.vehicles.mercedeseq.config import MercedesEQSoc
from modules.common import req
from paho.mqtt import publish as publish

ramdiskdir = '/var/www/html/openWB/ramdisk/'
moduledir = '/var/www/html/openWB/packages/modules/vehicles/mercedeseq/'

req_timeout = (30, 30)  # timeout for requests in seconds

vehicle = None

tok_url = "https://ssoalpha.dvb.corpinter.net/v1/token"
soc_url_pre_vin = "https://api.mercedes-benz.com/vehicledata/v2/vehicles/"
soc_url_post_vin = "/containers/electricvehicle"

log = logging.getLogger("soc."+__name__)

soc = None
range = None
timestamp = None


def handleResponse(what, status_code, text):
    if status_code == 204:
        # this is not an error code. Nothing to fetch so nothing to update
        log.error(what + " Request Code: " + str(status_code) +
                    " (no data is available for the resource)")
        log.error(text)
    elif status_code == 400:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (Bad Request)")
        log.error(text)

    elif status_code == 401:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (Invalid or missing authorization in header)")
        log.error(text)

    elif status_code == 402:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (Payment required)")
        log.error(text)

    elif status_code == 403:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (Forbidden)")
        log.error(text)

    elif status_code == 404:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (The requested resource was not found, e.g.: the selected vehicle could not be found)")
        log.error(text)

    elif status_code == 429:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (The service received too many requests in a given amount of time)")
        log.error(text)

    elif status_code == 500:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (The service received too many requests in a given amount of time)")
        log.error(text)

    elif status_code == 503:
        log.error(what + " Request fehlgeschlagen Code: " + str(status_code) +
                    " (The server is unable to service the request due to a temporary unavailability condition)")
        log.error(text)

    else:
        log.error(what + " Request fehlgeschlagen unbekannter Code: " + str(status_code))
        log.error(text)


def fetch_soc(config: MercedesEQSoc,
              vehicle_id: int) -> Tuple[float, float]:

    client_id = config.configuration.client_id
    client_secret = config.configuration.client_secret
    vin = config.configuration.vin
    soc_url = soc_url_pre_vin + str(vin) + soc_url_post_vin
    vehicle = vehicle_id
    log.info("client: " + client_id)

    log.debug("SOC URL: " + soc_url)

    # get Access Token from Broker
    access_token = config.configuration.token.access_token
    refresh_token = config.configuration.token.refresh_token
    expires_in = config.configuration.token.expires_in
    log.debug("Conf Access Tok: " + access_token)
    log.debug("Conf Refresh Tok: " + refresh_token)
    log.debug("Conf Expires_in: " + str(expires_in))

    log.info("Token expires in: " + str(int(expires_in) - int(time.time())) + "s. at: " +
                time.strftime("%d.%m.%Y  %H:%M:%S", time.localtime(expires_in)))

    if int(expires_in) < int(time.time()):
        # Access Token is exired
        log.info("Acc Token Expired")

        # get new Access Token with referesh token
        data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}
        
        ref = req.get_http_session().post(tok_url, data=data, verify=True, allow_redirects=False,
                                          auth=(client_id, client_secret), timeout=req_timeout)


        # write HTTP reponse code to file
        
        if ref.status_code == 200:
            # valid response
            tok = json.loads(ref.text)

            access_token = tok['access_token']
            refresh_token = tok['refresh_token']
            expires_in = tok['expires_in'] - 60 + int(time.time())
            id_token = tok['id_token']
            token_type = tok['token_type']

            # write new tokens

            config.configuration.token.access_token = access_token
            config.configuration.token.refresh_token = refresh_token
            config.configuration.token.expires_in = expires_in
            config.configuration.token.id_token = id_token
            config.configuration.token.token_type = token_type
            to_mqtt = json.dumps(config.__dict__, default=lambda o: o.__dict__)
            log.info("Config to MQTT:" + str(to_mqtt))
            publish.single("openWB/set/vehicle/" + vehicle + "/soc_module/config",
                           to_mqtt, retain=True, hostname="localhost")

        else:
            handleResponse("Refresh", ref.status_code, ref.text)

    # call API for SoC
    header = {'authorization': 'Bearer ' + access_token}
    
    try:
        req_soc = req.get_http_session().get(soc_url, headers=header, verify=True)
    except Timeout:
        log.ecxeption("Soc Request Timed Out")
    except RequestException:
        log.exception("Soc Request Request Exception occured " + soc_url)

    if req_soc.status_code == 200:
        # valid Response
        try:
            res = json.loads(req_soc.text)
        except JSONDecodeError:
            log.exception("Soc Response NO VALID JSON " + req_soc.text)

        # Extract SoC value and write to file
        for entry in res:
            for values in entry:
                if values == "soc":
                    soc = entry[values]['value']
                    # timestamp = entry[values]['timestamp']
                elif values == "rangeelectric":
                    range = entry[values]['value']
                else:
                    log.info("unknown entry: " + entry)
        if not soc:
            log.error("SoC Value not filled " + req_soc.text)
            soc = "0"
        if not range:
            log.error("RangeElectric Value not filled " + req_soc.text)
            range = "0"
        
        return float(soc), float(range)
    else:
        handleResponse("SoC", req_soc.status_code, req_soc.text)
        return 0, 0
