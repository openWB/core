#!/usr/bin/env python3

import logging
from typing import Union
import asyncio
from json import loads, dumps
from modules.vehicles.ovms.config import OVMS
from helpermodules.pub import Pub
from modules.common import req
from copy import deepcopy

TOKEN_CMD = "/api/token"
STATUS_CMD = "/api/status"
OVMS_APPL_LABEL = "application"
OVMS_APPL_VALUE = "owb-ovms-2.x-vh"
OVMS_PURPOSE_LABEL = "purpose"
OVMS_PURPOSE_VALUE = "get soc"

log = logging.getLogger(__name__)


# store soc module configuration
def write_config(topic: str, config: dict):
    try:
        log.debug("write_config:\n" + dumps(config, ensure_ascii=False, indent=4))
        Pub().pub(topic, config)
    except Exception as e:
        log.exception('Token mqtt write exception ' + str(e))


class api:

    def __init__(self):
        self.session = req.get_http_session()

    # create a new token and store it in the soc_module configuration
    def create_token(self) -> str:
        token_url = f"{self.server_url}{TOKEN_CMD}"
        data = {
            "username": self.user_id,
            "password": self.password
        }
        form_data = {
            OVMS_APPL_LABEL: self.ovms_appl_value,
            OVMS_PURPOSE_LABEL: OVMS_PURPOSE_VALUE
        }
        try:
            resp = self.session.post(token_url, params=data, files=form_data)
        except Exception as e:
            resp = e.response

        log.debug("create_token status_code=" + str(resp.status_code))
        tokenDict = loads(resp.text)
        log.debug("create_token response=" + dumps(tokenDict, indent=4))
        self.token = tokenDict['token']
        log.debug("create_token confDict=" + dumps(self.confDict, indent=4))
        self.confDict["configuration"]["token"] = resp.text.rstrip()
        cfg_setTopic = "openWB/set/vehicle/" + str(self.vehicle) + "/soc_module/config"
        write_config(cfg_setTopic, self.confDict)

        return self.token

    # check list of token on OVMS server for unused token created by the soc mudule
    # if any obsolete token are found these are deleted.
    def cleanup_token(self):
        tokenlist_url = f"{self.server_url}{TOKEN_CMD}?username={self.user_id}&password={self.token}"

        try:
            resp = self.session.get(tokenlist_url)
        except Exception as e:
            log.error("cleanup_token: exception = " + str(e))
            resp = e.response

        status_code = resp.status_code
        if status_code > 299:
            log.error("cleanup_token status_code=" + str(status_code))
            full_tokenlist = {}
        else:
            response = resp.text
            full_tokenlist = loads(response)
            log.debug("cleanup_token status_code=" +
                      str(status_code) + ", full_tokenlist=\n" +
                      dumps(full_tokenlist, indent=4))
            obsolete_tokenlist = list(filter(lambda token:
                                             token[OVMS_APPL_LABEL] == self.ovms_appl_value
                                             and token["token"] != self.token,
                                             full_tokenlist))
            if len(obsolete_tokenlist) > 0:
                log.debug("cleanup_token obsolete_tokenlist=\n" + dumps(obsolete_tokenlist, indent=4))
                for tok in obsolete_tokenlist:
                    token_to_delete = tok["token"]
                    log.debug("cleanup_token: token_to_delete=" + dumps(tok, indent=4))
                    token_del_url = f"{self.server_url}{TOKEN_CMD}/{token_to_delete}"
                    token_del_url = f"{token_del_url}?username={self.user_id}&password={self.token}"
                    try:
                        resp = self.session.delete(token_del_url)
                    except Exception as e:
                        log.error("delete_token: exception = " + str(e))
                        resp = e.response

                    status_code = resp.status_code
            else:
                log.debug("cleanup_token: no obsolete token found")

        return

    # get status for vehicleId
    def get_status(self) -> Union[int, dict]:
        status_url = f"{self.server_url}{STATUS_CMD}/{self.vehicleId}?username={self.user_id}&password={self.token}"

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

    # async function to fetch soc, range, soc_ts
    async def _fetch_soc(self,
                         conf: OVMS,
                         vehicle: int) -> Union[int, float, str, float, float]:
        self.config_topic = "openWB/set/vehicle/" + vehicle + "/soc_module/config"
        self.server_url = conf.configuration.server_url
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vehicleId = conf.configuration.vehicleId
        self.vehicle = vehicle
        self.ovms_appl_value = OVMS_APPL_VALUE + str(self.vehicle)
        self.config = deepcopy(conf)
        self.confDict = self.config.__dict__
        self.confDict["configuration"] = self.config.configuration.__dict__
        log.debug("self.confDict2=" + dumps(self.confDict, indent=4))

        if 'token' in self.confDict['configuration']:
            tokenstr = self.confDict['configuration']['token']
            log.debug("read tokenstr (" + str(tokenstr) + ") from configuration")
        else:
            tokenstr = ""
            log.debug("init tokenstr to (" + str(tokenstr) + ")")
        log.debug("tokenstr=" + str(tokenstr))

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

        self.cleanup_token()

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

        self.kms = float(statusDict['odometer']) / 10
        self.vehicle12v = statusDict['vehicle12v']
        self.soc_ts = statusDict['m_msgtime_s']

        return int(float(self.soc)), float(self.range), self.soc_ts


# sync function
def fetch_soc(conf: OVMS, vehicle: int) -> Union[int, float, str]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = api()
    soc, range, soc_ts = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range, soc_ts
