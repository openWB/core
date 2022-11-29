#!/usr/bin/env python3

import logging
from typing import Union
from modules.vehicles.vwid import libvwid
import aiohttp
import asyncio
# import datetime
import time
# import jwt
import json
from modules.common.store import RAMDISK_PATH
from modules.vehicles.vwid.config import VWId
from modules.vehicles.vwid.socutils import socUtils

date_fmt = '%Y-%m-%d %H:%M:%S'
refreshToken_exp_days = 7    # 7 days before refreshToken expires a new refreshToken shall be stored
initialToken = '1.2.3'

log = logging.getLogger("soc."+__name__)


class api:

    def __init__(self):
        self.su = socUtils()
        pass

    # async method, called from sync fetch_soc, required because libvwid expects  async enviroment
    async def _fetch_soc(self,
                         conf: VWId,
                         vehicle: int) -> Union[int, float]:
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.refreshToken = conf.configuration.refreshToken
        self.replyFile = 'soc_vwid_reply_vh_' + str(vehicle)
        self.accessTokenFile = str(RAMDISK_PATH) + '/soc_vwid_accessToken_vh_' + str(vehicle)
        self.accessToken_old = {}

        async with aiohttp.ClientSession() as self.session:
            self.w = libvwid.vwid(self.session)
            self.w.set_vin(self.vin)
            self.w.set_credentials(self.user_id, self.password)
            self.w.tokens = {}
            self.w.headers = {}

            # initialize refreshToken
            try:
                if self.refreshToken is None:
                    log.debug("set refreshToken to initial value")
                    self.w.tokens['refreshToken'] = initialToken
                else:
                    self.w.tokens['refreshToken'] = self.refreshToken

            except Exception:
                log.debug("refreshToken initialization exception: set refreshToken_old to initial value")
                self.w.tokens['refreshToken'] = initialToken

            self.refreshTokenOld = self.w.tokens['refreshToken']   # remember current refreshToken

            # initialize accessToken
            self.accessTokenOld = self.su.read_token_file(self.accessTokenFile)
            if self.accessTokenOld is None:
                log.debug('set accessToken to initial value')
                self.accessTokenOld = initialToken
            self.w.tokens['accessToken'] = self.accessTokenOld     # initialize tokens in vwid
            self.w.headers['Authorization'] = 'Bearer %s' % self.w.tokens["accessToken"]

            # get status from VW server
            self.data = await self.w.get_status()
            if (self.data):
                try:
                    if self.data['error'] != {}:
                        log.error("server error: \n" + json.dumps(self.data['error'], ensure_ascii=False, indent=4))
                    if self.data['data'] != {}:
                        log.debug("batteryStatus: \n" +
                                  json.dumps(self.data['data']['batteryStatus'], ensure_ascii=False, indent=4))
                except Exception as e:
                    log.error("response decode error: " + str(e))
                    log.error("response: \n" + json.dumps(self.data, ensure_ascii=False, indent=4))

                try:
                    self.soc = (self.data['data']['batteryStatus']['currentSOC_pct'])
                    self.range = float(self.data['data']['batteryStatus']['cruisingRangeElectric_km'])
                except Exception as e:
                    log.debug("soc/range field missing exception: e=" + str(e))
                    self.soc = 0
                    self.range = 0.0

                # decision logic - shall a new refreshToken be stored?
                self.store_refreshToken = False
                self.refreshTokenNew = self.w.tokens['refreshToken']

                if self.refreshTokenOld != initialToken:
                    try:
                        # self.refreshTokenOld_dec =\
                        #     jwt.decode(self.refreshTokenOld, 'utf-8', options={"verify_signature": False})
                        # self.expOld = self.refreshTokenOld_dec['exp']
                        # self.expOld_dt = datetime.datetime.fromtimestamp(self.expOld).strftime(date_fmt)

                        self.expOld, self.expOld_dt = self.su.get_token_expiration(self.refreshTokenOld, date_fmt)
                        self.now = int(time.time())
                        expirationThreshold = self.expOld - refreshToken_exp_days * 86400

                        if expirationThreshold < self.now:
                            log.debug('RefreshToken: expiration in less than ' +
                                      str(refreshToken_exp_days) + ' days on ' + self.expOld_dt + ', store new token')
                            self.store_refreshToken = True
                    except Exception as e:
                        log.debug("refreshToken decode exception: e=" + str(e))
                        self.store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

                    else:
                        log.debug("Old refreshToken expires on " + self.expOld_dt + ", keep it")
                else:
                    self.store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

                if self.store_refreshToken:          # refreshToken needs to be stored in config json
                    try:
                        # self.refreshTokenNew_dec =\
                        #     jwt.decode(self.refreshTokenNew, 'utf-8', options={"verify_signature": False})
                        # self.expNew = self.refreshTokenNew_dec['exp']
                        # self.expNew_dt = datetime.datetime.fromtimestamp(self.expNew).strftime(date_fmt)

                        self.expNew, self.expNew_dt = self.su.get_token_expiration(self.refreshTokenNew, date_fmt)
                        log.debug("store new refreshToken, expires on " + self.expNew_dt)
                    except Exception as e:
                        log.debug("new refreshToken decode exception, e=" + str(e))
                        log.debug("new refreshToken=" + str(self.refreshTokenNew))

                    confDict = conf.__dict__
                    confDict.pop('name')
                    confDict['configuration'] = conf.configuration.__dict__
                    self.su.write_token_mqtt(
                                             "openWB/set/vehicle/" + vehicle + "/soc_module/config",
                                             self.refreshTokenNew,
                                             conf.__dict__)

                if (self.w.tokens['accessToken'] != self.accessTokenOld):  # modified accessToken?
                    self.su.write_token_file(self.accessTokenFile, self.w.tokens['accessToken'])

                return self.soc, self.range


def fetch_soc(conf: VWId, vehicle: int) -> Union[int, float]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    a = api()
    soc, range = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range
