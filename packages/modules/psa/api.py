#!/usr/bin/env python3

from typing import Union
import logging
import os
import json
import urllib
import requests
import base64
from modules.common.store import RAMDISK_PATH
# currently unused
# import sys
# import time
# import getopt
# import getpass
# import http.client as http_client

log = logging.getLogger("soc."+__name__)

# these two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.


def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout
    try:
        f = open(replyFile, 'w', encoding='utf-8')
    except Exception as e:
        log.debug("psa.dump_json: chmod File" + replyFile + ", exception, e=" + str(e))
        os.system("sudo rm " + replyFile)
        f = open(replyFile, 'w', encoding='utf-8')
    json.dump(data, f, ensure_ascii=False, indent=4)
    f.close()


def requestPSAData(userid: str,
                   password: str,
                   client_id: str,
                   client_secret: str,
                   manufacturer: str,
                   soccalc: str,
                   vehicle: int) -> dict:

    # Step1: Authentication: get access_token
    userpass = client_id + ':' + client_secret
    encoded_u = base64.b64encode(userpass.encode()).decode()
    # header1 = str('Basic %s' % encoded_u)
    scope = 'openid profile'
    if (manufacturer == "Peugeot"):
        brand = 'peugeot.com'
        realm = 'clientsB2CPeugeot'
    elif (manufacturer == "Citroen"):
        brand = 'citroen.com'
        realm = 'clientsB2CCitroen'
    elif (manufacturer == "DS"):
        brand = 'driveds.com'
        realm = 'clientsB2CDS'
    elif (manufacturer == "Opel"):
        brand = 'opel.com'
        realm = 'clientsB2COpel'
    elif (manufacturer == "Vauxhall"):
        brand = 'vauxhall.co.uk'
        realm = 'clientsB2CVauxhall'
    # vin = '?'
    data = {'realm': realm, 'grant_type': 'password', 'password': password, 'username': userid, 'scope': scope}
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic %s' % encoded_u}
    reg = 'https://idpcvs.' + brand + '/am/oauth2/access_token'
    dmp = {}   # dump request 1
    dmp['reg'] = reg
    dmp['data'] = data
    dmp['headers'] = headers
    dump_json(dmp, "/psareq1vh" + str(vehicle))
    response = requests.post(reg, data=data, headers=headers)
    responsetext = response.text
    responsestatus = response.status_code
    dmp = {}   # dump response 1
    dmp['text'] = str(responsetext.encode("utf-8"))
    dmp['status'] = str(responsestatus)
    dump_json(dmp, "/psareply1vh" + str(vehicle))
    psa_config = json.loads(responsetext)
    acc_token = psa_config['access_token']

    # step2:  get list of vehicles? vin_vin - not used anywhere?
    payload = {'client_id': client_id}
    data = urllib.urlencode(payload)
    data = data.encode('Big5')
    reg = 'https://api.groupe-psa.com/connectedcar/v4/user/vehicles?' + data
    headers = {'Accept': 'application/hal+json', 'Authorization': 'Bearer %s' % acc_token, 'x-introspect-realm': realm}
    dmp = {}   # dump request 2
    dmp['reg'] = reg
    dmp['data'] = data
    dmp['headers'] = headers
    dump_json(dmp, "/psareq2vh" + str(vehicle))
    response = requests.get(reg, headers=headers)
    responsetext = response.text
    responsestatus = response.status_code
    dmp = {}   # dump response 2
    dmp['text'] = str(responsetext.encode("utf-8"))
    dmp['status'] = str(responsestatus)
    dump_json(dmp, "/psareply2vh" + str(vehicle))
    vin_list = json.loads(responsetext)
    vin_id = vin_list['_embedded']['vehicles'][0]['id']
    # vin_vin = vin_list['_embedded']['vehicles'][0]['vin']

    # step3: get batt, list of vehicles?
    payload = {'client_id': client_id}
    data = urllib.urlencode(payload)
    data = data.encode('Big5')
    # --'/user/vehicles/{id}/status'
    reg = 'https://api.groupe-psa.com/connectedcar/v4/user/vehicles/' + vin_id + '/status?' + data
    headers = {'Accept': 'application/hal+json', 'Authorization': 'Bearer %s' % acc_token, 'x-introspect-realm': realm}
    dmp = {}   # dump request 3
    dmp['reg'] = reg
    dmp['data'] = data
    dmp['headers'] = headers
    dump_json(dmp, "/psareq3vh" + str(vehicle))
    response = requests.get(reg, headers=headers)
    responsetext = response.text
    responsestatus = response.status_code
    dmp = {}   # dump response 3
    dmp['text'] = str(responsetext.encode("utf-8"))
    dmp['status'] = str(responsestatus)
    dump_json(dmp, "/psareply3vh" + str(vehicle))
    batt = json.loads(responsetext)

    # filter to only include type=Electric but remove all others. Seen type=Fuel and type=Electric being returned.
    batt = filter(lambda x: x['type'] == 'Electric', batt['energy'])
    soc = batt[0]['level']
    # !!!!!!In batt herausfinden, in welchem feld die Reichweite steht
    range = batt[0]['range']

# comment the manual calculation section for now
#    if (int(soccalc) == 0):
#        # manual calculation not enabled, using existing logic
#        if (int(str(vehicle)) == 1):
#            f = open('/var/www/html/openWB/ramdisk/soc', 'w')
#        if (int(str(vehicle)) == 2):
#            f = open('/var/www/html/openWB/ramdisk/soc1', 'w')
#        f.write(str(soc))
#        f.close()
#    else:
#        # manual calculation  enabled, using new logic with timestamp
#        if (int(str(vehicle)) == 1):
#            f = open('/var/www/html/openWB/ramdisk/psasoc', 'w')
#        if (int(str(vehicle)) == 2):
#            f = open('/var/www/html/openWB/ramdisk/psasoc1', 'w')
#        f.write(str(soc))
#        f.close()
#        # getting timestamp of fetched SoC
#        fetchedsoctime = batt[0]['updatedAt']
#        soct = time.strptime(fetchedsoctime, "%Y-%m-%dT%H:%M:%SZ")
#        soctime = time.mktime(soct)
#        # adding one hour to UTC to get CET
#        soctime = soctime + 3600
#        # checking for daylight saving time
#        dst = time.localtime()
#        if (dst.tm_isdst == 1):
#            # adding one hour to fetched SoCtime in daylight saving time
#            soctime = soctime + 3600
#        # writing timestamp to ramdisk
#        if (int(str(vehicle)) == 1):
#            f = open('/var/www/html/openWB/ramdisk/psasoctime', 'w')
#        if (int(str(vehicle)) == 2):
#            f = open('/var/www/html/openWB/ramdisk/psasoctime1', 'w')
#        f.write(str(int(soctime)))
#        f.close()
    return soc, range


def fetch_soc(userid: str,
              password: str,
              client_id: str,
              client_secret: str,
              manufacturer: str,
              soccalc: str,
              vin: str,
              vehicle: int) -> Union[int, float]:

    try:
        log.info("psa:fetch_soc: userid=" + userid)
        log.info("psa:fetch_soc: password=" + password)
        log.info("psa:fetch_soc: client_id=" + client_id)
        log.info("psa:fetch_soc: client_secret=" + client_secret)
        log.info("psa:fetch_soc: manufacturer=" + manufacturer)
        log.info("psa:fetch_soc: soccalc=" + soccalc)
        log.info("psa:fetch_soc: vin=" + vin)
        log.info("psa:fetch_soc: vehicle=" + vehicle)
        soc, range = requestPSAData(userid, password, client_id, client_secret, manufacturer, soccalc, vehicle)
    except Exception as err:
        log.error("psa.fetch_soc: requestData Error, vehicle: " + str(vehicle) + f" {err=}, {type(err)=}")
        raise
    log.info("psa.fetch_soc: soc=" + str(soc) + "%, range=" + str(range))
    return soc, range
