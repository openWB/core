#!/usr/bin/env python3

import logging
from typing import Union
import asyncio
from json import loads, dumps
from modules.vehicles.ovms.config import OVMS
from helpermodules.pub import Pub
from modules.common import req

OVMS_SERVER = "https://ovms.dexters-web.de:6869"
TOKEN_CMD = "/api/token"
STATUS_CMD = "/api/status"

log = logging.getLogger(__name__)


def write_config(topic: str, config: dict):
    try:
        log.debug("write_config:\n" + dumps(config, ensure_ascii=False, indent=4))
        Pub().pub(topic, config)
    except Exception as e:
        log.exception('Token mqtt write exception ' + str(e))


class api:

    def __init__(self):
        self.session = req.get_http_session()
        pass

    def create_token(self) -> str:
        token_url = f"{OVMS_SERVER}{TOKEN_CMD}"
        data = {
            "username": self.user_id,
            "password": self.password
        }
        form_data = {
            "application": "owb-ovms",
            "purpose": "get soc"
        }
        try:
            resp = self.session.post(token_url, params=data, files=form_data)
        except Exception as e:
            resp = e.response

        log.debug("create_token status_code=" + str(resp.status_code))
        tokenDict = loads(resp.text)
        log.debug("create_token response=" + dumps(tokenDict, indent=4))
        self.token = tokenDict['token']
        confDict = self.config.__dict__
        confDict["configuration"] = self.config.configuration.__dict__
        log.debug("create_token confDict=" + dumps(confDict, indent=4))
        confDict["configuration"]["token"] = resp.text.rstrip()
        cfg_setTopic = "openWB/set/vehicle/" + str(self.vehicle) + "/soc_module/config"
        write_config(
            cfg_setTopic,
            confDict)
        return self.token

    # get status for vehicleId
    def get_status(self) -> Union[int, dict]:
        status_url = f"{OVMS_SERVER}{STATUS_CMD}/{self.vehicleId}?username={self.user_id}&password={self.token}"

        log.debug("status-url=" + status_url)
        try:
            resp = self.session.get(status_url)
        except Exception as e:
            resp = e.response

        status_code = resp.status_code
        if status_code > 299:
            log.error("get_status status_code=" + str(status_code) + ", create new token")
            respDict = {}
        else:
            response = resp.text
            respDict = loads(response)
            log.debug("get_status status_code=" + str(status_code) + ", response=" + dumps(respDict, indent=4))
        return int(status_code), respDict

    async def _fetch_soc(self,
                         conf: OVMS,
                         vehicle: int) -> Union[int, float, str]:
        self.config_topic = "openWB/set/vehicle/" + vehicle + "/soc_module/config"
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vehicleId = conf.configuration.vehicleId
        self.vehicle = vehicle
        # self.config = conf.configuration
        self.config = conf
        tokenstr = self.config.configuration.token
        if tokenstr is None or tokenstr == "":
            self.token = self.create_token()
        else:
            log.debug("_fetch_soc tokenstr=\n" + tokenstr)
            tokDict = loads(tokenstr)
            log.debug("_fetch_soc tokDict=\n" + dumps(tokDict, indent=4))
            self.token = tokDict['token']

        if self.token is None or self.token == "":
            self.token = self.create_token()
        else:
            log.debug("_fetch_soc using token=" + self.token)

        status_code, statusDict = self.get_status()
        if status_code > 299:
            self.token = self.create_token()
            status_code, statusDict = self.get_status()
            if status_code > 299:
                raise f"Authentication Problem, status_code {status_code}"

        self.soc = statusDict['soc']
        self.range = statusDict['estimatedrange']
        # handle potential bug in OVMS, sometimes range is too high by factor 10
        if float(self.range) > 1000.0:
            self.range = str(float(self.range) / 10)
        self.soc_ts = statusDict['m_msgtime_s']
        log.debug("soc=" + str(self.soc) + ", range=" + str(self.range) + ", soc_ts=" + str(self.soc_ts))

        return int(float(self.soc)), float(self.range), self.soc_ts


def fetch_soc(conf: OVMS, vehicle: int) -> Union[int, float, str]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = api()
    soc, range, soc_ts = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range, soc_ts
