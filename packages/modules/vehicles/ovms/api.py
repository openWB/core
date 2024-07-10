#!/usr/bin/env python3

import logging
from typing import Union
import requests
# from requests.auth import HTTPBasicAuth
import asyncio
import time
from datetime import datetime
from json import loads, dumps, dump
from modules.common.store import RAMDISK_PATH
from modules.vehicles.ovms.config import OVMS
from helpermodules.pub import Pub
from control import data
from modules.common.configurable_vehicle import ConfigurableVehicle

OVMS_SERVER = "https://ovms.dexters-web.de:6869"
TOKEN_CMD = "/api/token"
STATUS_CMD = "/api/status"

date_fmt = '%Y-%m-%d %H:%M:%S'
ts_fmt = '%Y-%m-%dT%H:%M:%S'
initialToken = '1.2.3'

log = logging.getLogger(__name__)


def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset


def write_config(topic: str, config: dict):
    try:
        log.debug("write_config:\n" + dumps(config, ensure_ascii=False, indent=4))
        Pub().pub(topic, config)
    except Exception as e:
        log.exception('Token mqtt write exception ' + str(e))


# get config of vehicle by number
def get_vehicle_config(vehicle: int) -> dict:
    try:
        ev_data = data.data.ev_data.copy()
        for ev in ev_data.values():
            if int(ev.num) == int(vehicle):
                cv: ConfigurableVehicle = ev.soc_module
                se = cv.vehicle_config.toJSON()
                break
        else:
            se = "{}"
            log.warn('get_vehicle_config: ev=' + str(vehicle) + ' not found')
    except Exception as e:
        se = "{}"
        log.warn('get_vehicle_config: Error: ' + str(e))
    sed = loads(se)
    return sed


def update_vehicle_config(vehicle: int, conf_update: dict):
    confDict = get_vehicle_config(vehicle)

    log.debug("update_vehicle_config: confDict_org=" + dumps(confDict, indent=4))
    # update values in conf_update
    for k, v in conf_update.items():
        confDict['configuration'][k] = v
    log.debug("update_vehicle_config: confDict_new=" + dumps(confDict, indent=4))
    cfg_setTopic = "openWB/set/vehicle/" + str(vehicle) + "/soc_module/config"
    write_config(
        cfg_setTopic,
        confDict)
    return


class api:

    def __init__(self):
        pass

    def create_token(self) -> str:
        token_url = OVMS_SERVER + TOKEN_CMD
        data = {
            "username": self.user_id,
            "password": self.password
        }
        form_data = {
            "application": "owb-ovms",
            "purpose": "get soc"
        }
        resp = requests.post(token_url, params=data, files=form_data)
        log.debug("token status_code=" + str(resp.status_code))
        log.debug("token resp.text=" + str(resp.text))
        tokenDict = loads(resp.text)
        log.debug("token-response=" + dumps(tokenDict, indent=4))
        self.token = tokenDict['token']
        log.debug("token=" + self.token)
        confUpdDict = {"token": resp.text.rstrip()}
        update_vehicle_config(self.vehicle, confUpdDict)
        return self.token

    # get status for vehicleId
    def get_status(self) -> dict:
        status_url = OVMS_SERVER + STATUS_CMD + "/" + self.vehicleId
        status_url = status_url + "?username=" + self.user_id
        status_url = status_url + "&password=" + self.token

        log.debug("status-url=" + status_url)
        resp = requests.get(status_url)
        status_code = resp.status_code
        response = resp.text
        respDict = loads(response)
        log.debug("status_code=" + str(status_code) + ", response=" + dumps(respDict, indent=4))
        return respDict

    async def _fetch_soc(self,
                         conf: OVMS,
                         vehicle: int) -> Union[int, float, str]:
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vehicleId = conf.configuration.vehicleId
        self.vehicle = vehicle
        tokenstr = conf.configuration.token

        log.debug("tokenstr=\n" + tokenstr)
        tokDict = loads(tokenstr)
        log.debug("tokDict=\n" + dumps(tokDict, indent=4))
        self.token = tokDict['token']
        self.replyFile = str(RAMDISK_PATH) + '/soc_ovms_reply_vh_' + str(vehicle) + '.json'
        self.config_topic = "openWB/set/vehicle/" + vehicle + "/soc_module/config"

        if self.token is None or self.token == "":
            self.token = self.create_token()
        else:
            log.debug("using token=" + self.token)

        statusDict = self.get_status()

        self.soc = statusDict['soc']
        self.range = statusDict['estimatedrange']
        self.soc_ts = statusDict['m_msgtime_s']
        log.debug("soc=" + str(self.soc) + ", range=" + str(self.range) + ", soc_ts=" + str(self.soc_ts))

        try:
            with open(self.replyFile, 'w', encoding='utf-8') as tf:
                dump(statusDict, tf, indent=4)
        except Exception as e:
            log.exception("write_json_file: " + self.replyFile + " Exception " + str(e))

        return int(float(self.soc)), float(self.range), self.soc_ts


def fetch_soc(conf: OVMS, vehicle: int) -> Union[int, float, str]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = api()
    soc, range, soc_ts = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range, soc_ts
