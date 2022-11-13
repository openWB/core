#!/usr/bin/env python3

from typing import Union
import os
import json
import urllib
import logging
from modules.common.store import RAMDISK_PATH

log = logging.getLogger("soc."+__name__)


def dump_json(data: dict, fout: str):
    if log.getEffectiveLevel() < 20:
        log.info("renault.fetch_soc: log.level=" + str(log.getEffectiveLevel()))
        jsonFile = str(RAMDISK_PATH) + '/' + fout
        try:
            f = open(jsonFile, 'w', encoding='utf-8')
        except Exception as e:
            log.debug("renault.dump_json: chmod File" + jsonFile + ", exception, e=" + str(e))
            os.system("sudo rm " + jsonFile)
            f = open(jsonFile, 'w', encoding='utf-8')
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.close()


def requestRENAULTData(userid: str, password: str, location: str, country: str, vin: str, vehicle: int) -> dict:

    # creates a request, not executed, as it is in the original code, we leave it here for now
    reg = 'https://renault-wrd-prod-1-euw1-myrapp-one.s3-eu-west-1'
    reg = reg + '.amazonaws.com/configuration/android/config_' + location + '.json'
    dmp = {}
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_1_request_vh" + str(vehicle))
    # response= urllib.request.urlopen(reg)
    # responsetext  = response.read()
    # dmp = {}
    # dmp['response'] = str(response)
    # dmp['responsetext'] = str(responsetext)
    # dump_json(dmp, "soc_renault_1_reply_vh" + str(vehicle))
    # android_config = json.loads(responsetext)
    # gigyarooturl = android_config['servers']['gigyaProd']['target']
    # gigyaapi = android_config['servers']['gigyaProd']['apikey']
    # kamereonrooturl = android_config['servers']['wiredProd']['target']
    # kamereonapikey = android_config['servers']['wiredProd']['apikey']
    gigyarooturl = 'https://accounts.eu1.gigya.com'
    gigyaapi = '3_7PLksOyBRkHv126x5WhHb-5pqC1qFR8pQjxSeLB6nhAnPERTUlwnYoznHSxwX668'
    kamereonrooturl = 'https://api-wired-prod-1-euw1.wrd-aws.com'
    kamereonapikey = 'VAX7XYKGfa92yMvXculCkEFyfZbuM7Ss'

    # Step 2
    payload = {'loginID': userid, 'password': password, 'apiKey': gigyaapi}
    data = urllib.parse.urlencode(payload)
    data = data.encode('Big5')
    reg = gigyarooturl + '/accounts.login?' + data.decode("utf-8")
    dmp = {}
    dmp['payload'] = str(payload)
    dmp['data'] = data.decode("utf-8")
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_2_request_vh" + str(vehicle))
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    dmp = {}
    dmp['response'] = str(response)
    dmp['responsetext'] = str(responsetext)
    dump_json(dmp, "soc_renault_2_reply_vh" + str(vehicle))

    # Step 3
    gigya_session = json.loads(responsetext)
    gigyacookievalue = gigya_session['sessionInfo']['cookieValue']
    payload = {'login_token': gigyacookievalue, 'apiKey': gigyaapi}
    data = urllib.parse.urlencode(payload)
    data = data.encode('Big5')
    reg = gigyarooturl + '/accounts.getAccountInfo?' + data.decode("utf-8")
    dmp = {}
    dmp['payload'] = str(payload)
    dmp['data'] = data.decode("utf-8")
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_3_request_vh" + str(vehicle))
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    dmp = {}
    dmp['response'] = str(response)
    dmp['responsetext'] = str(responsetext)
    dump_json(dmp, "soc_renault_3_reply_vh" + str(vehicle))

    # Step 4
    gigya_account = json.loads(responsetext)
    kamereonpersonid = gigya_account['data']['personId']
    payload = {'login_token': gigyacookievalue, 'apiKey': gigyaapi,
               'fields': 'data.personId,data.gigyaDataCenter', 'expiration': 900}
    data = urllib.parse.urlencode(payload)
    data = data.encode('Big5')
    reg = gigyarooturl + '/accounts.getJWT?' + data.decode("utf-8")
    dmp = {}
    dmp['payload'] = str(payload)
    dmp['data'] = data.decode("utf-8")
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_4_request_vh" + str(vehicle))
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    dmp = {}
    dmp['response'] = str(response)
    dmp['responsetext'] = str(responsetext)
    dump_json(dmp, "soc_renault_4_reply_vh" + str(vehicle))

    # Step 5
    gigya_jwt = json.loads(responsetext)
    gigya_jwttoken = gigya_jwt['id_token']
    payload = {'country': country}
    data = urllib.parse.urlencode(payload)
    data = data.encode('Big5')
    reg = urllib.request.Request(kamereonrooturl + '/commerce/v1/persons/' +
                          kamereonpersonid + '?' + data.decode("utf-8"))
    reg.add_header('x-gigya-id_token', gigya_jwttoken)
    reg.add_header('apikey', kamereonapikey)
    dmp = {}
    dmp['data'] = data.decode("utf-8")
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_5_request_vh" + str(vehicle))
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    dmp = {}
    dmp['response'] = str(response)
    dmp['responsetext'] = str(responsetext)
    dump_json(dmp, "soc_renault_5_reply_vh" + str(vehicle))
    kamereon_per = json.loads(responsetext)
    kamereonaccountid = kamereon_per['accounts'][0]['accountId']

    # Step 6 - skipped
    # print(time_string,'kamereonaccountid',kamereonaccountid)
    # payload = {'country': country}
    # headers = {'x-gigya-id_token': gigya_jwttoken, 'apikey': kamereonapikey}
    # data = urllib.parse.urlencode(payload)
    # data = data.encode('Big5')
    # reg = urllib.request.Request(kamereonrooturl + '/commerce/v1/accounts/'
    # + kamereonaccountid + '/kamereon/token?'  + data.decode("utf-8"))
    # reg.add_header('x-gigya-id_token',gigya_jwttoken)
    # reg.add_header('apikey', kamereonapikey)
    # print('c6',reg)
    # response= urllib.request.urlopen(reg)
    # responsetext  = response.read()
    # dmp = {}
    # dmp['response'] = str(response)
    # dmp['responsetext'] = str(responsetext)
    # dump_json(dmp, "soc_renault_6_reply_vh" + str(vehicle))
    # kamereon_token = json.loads(responsetext)
    # kamereonaccesstoken = kamereon_token['accessToken']
    # print(time_string,'kamereonaccesstoken',kamereonaccesstoken)

    # Step 7 - vehicles
    payload = {'country': country}
    data = urllib.parse.urlencode(payload)
    data = data.encode('Big5')
    reg = urllib.request.Request(kamereonrooturl + '/commerce/v1/accounts/' +
                          kamereonaccountid + '/vehicles?' + data.decode("utf-8"))
    reg.add_header('x-gigya-id_token', gigya_jwttoken)
    reg.add_header('apikey', kamereonapikey)
    dmp = {}
    dmp['payload'] = str(payload)
    dmp['data'] = data.decode("utf-8")
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_7_request_vh" + str(vehicle))
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    vehic = json.loads(responsetext)
    dmp = {}
    dmp['response'] = str(response)
    dmp['responsetext'] = str(responsetext)
    dmp['vehic'] = str(vehic)
    dump_json(dmp, "soc_renault_7_reply_vh" + str(vehicle))
    if len(vin) < 10:
        vin = vehic['vehicleLinks'][0]['vin']

    # Step 8 - battery-status
    payload = {'country': country}
    data = urllib.parse.urlencode(payload)
    data = data.encode('Big5')
    reg = urllib.request.Request(kamereonrooturl + '/commerce/v1/accounts/' +
                          kamereonaccountid + '/kamereon/kca/car-adapter/v2/cars/'
                          + vin + '/battery-status?' + data.decode("utf-8"))
    reg.add_header('x-gigya-id_token', gigya_jwttoken)
    reg.add_header('apikey', kamereonapikey)
    dmp = {}
    dmp['payload'] = str(payload)
    dmp['data'] = data.decode("utf-8")
    dmp['reg'] = str(reg)
    dump_json(dmp, "soc_renault_8_request_vh" + str(vehicle))
    response = urllib.request.urlopen(reg)
    responsetext = response.read()
    batt = json.loads(responsetext)
    soc = batt['data']['attributes']['batteryLevel']
    range = batt['data']['attributes']['batteryAutonomy']
    dmp = {}
    dmp['response'] = str(response)
    dmp['responsetext'] = str(responsetext)
    dmp['batt'] = batt
    dmp['soc'] = soc
    dmp['range'] = range
    dump_json(dmp, "soc_renault_8_reply_vh" + str(vehicle))
    return int(soc), float(range)


def fetch_soc(userid: str, password: str, location: str, country: str, vin: str, vehicle: int) -> Union[int, float]:
    # log.info("renault.fetch_soc: userid=" + userid)
    # log.info("renault.fetch_soc: password=" + password)
    # log.info("renault.fetch_soc: location=" + location)
    # log.info("renault.fetch_soc: country=" + country)
    # log.info("renault.fetch_soc: vin=" + vin)
    # log.info("renault.fetch_soc: vehicle=" + str(vehicle))

    try:
        soc, range = requestRENAULTData(userid, password, location, country, vin, vehicle)
    except Exception as err:
        log.error("renault.fetch_soc: requestData Error, vehicle: " + str(vehicle) + f" {err=}, {type(err)=}")
        raise
    log.info("renault.fetch_soc: vehicle: " + str(vehicle) + ", soc=" + str(soc) + "%, range=" + str(range))
    return soc, range
