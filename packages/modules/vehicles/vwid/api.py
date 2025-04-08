#!/usr/bin/env python3

from logging import getLogger
from typing import Union
from modules.vehicles.vwid import libvwid
from modules.vehicles.vwid import libskoda
import aiohttp
from asyncio import new_event_loop, set_event_loop
from time import time, mktime
from datetime import datetime
from json import dumps
from modules.common.store import RAMDISK_PATH
from modules.vehicles.vwid.config import VWId
from modules.vehicles.vwid.socutils import socUtils

date_fmt = '%Y-%m-%d %H:%M:%S'
ts_fmt = '%Y-%m-%dT%H:%M:%S'
refreshToken_exp_days = 7    # 7 days before refreshToken expires a new refreshToken shall be stored
initialToken = '1.2.3'

log = getLogger(__name__)


# convert utc timestamp to local time
def utc2local(utc):
    epoch = mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset


class api:

    def __init__(self):
        self.su = socUtils()
        pass

    # async method, called from sync fetch_soc, required because libvwid/libskoda expect async environment
    async def _fetch_soc(self,
                         conf: VWId,
                         vehicle: int) -> Union[int, float, str]:
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.refreshToken = conf.configuration.refreshToken
        self.replyFile = 'soc_vwid_reply_vh_' + str(vehicle)
        self.accessTokenFile = str(RAMDISK_PATH) + '/soc_vwid_accessToken_vh_' + str(vehicle)
        self.accessToken_old = {}

        brand = self.vin[:3]
        log.info("brand = " + brand)
        if brand == "WVW":
            self.brand = "vwid"
        elif brand == "TMB":
            self.brand = "skoda"
        else:
            log.error("Brand " + brand + " is not one of WVW, TMB")
            self.soc = 0
            self.range = 0.0
            self.soc_ts = ""
            self.soc_tsX = time()
            return self.soc, self.range, self.soc_ts, self.soc_tsX

        async with aiohttp.ClientSession() as self.session:
            if self.brand == "vwid":
                self.w = libvwid.vwid(self.session)
            elif self.brand == "skoda":
                self.w = libskoda.vwid(self.session)
            else:
                log.error("Brand " + self.brand + " is not one of vwid, skoda")

            self.w.set_vin(self.vin)
            self.w.set_credentials(self.user_id, self.password)
            self.w.set_jobs(['charging'])
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
                if self.su.keys_exist(self.data, 'userCapabilities', 'capabilitiesStatus', 'error'):
                    log.error("Server Error: \n"
                              + dumps(self.data['userCapabilities']['capabilitiesStatus']['error'],
                                      ensure_ascii=False, indent=4))

                if self.brand == "vwid":
                    if self.su.keys_exist(self.data, 'charging', 'batteryStatus'):
                        log.debug("batteryStatus: \n" +
                                  dumps(self.data['charging']['batteryStatus'],
                                        ensure_ascii=False, indent=4))
                elif self.brand == "skoda":
                    if self.su.keys_exist(self.data, 'primaryEngineRange'):
                        log.debug("batteryStatus: \n" +
                                  dumps(self.data['primaryEngineRange'],
                                        ensure_ascii=False, indent=4))
                else:
                    log.error("Brand " + self.brand + " is not one of vwid, skoda")

                try:
                    if self.brand == "vwid":
                        self.soc = int(self.data['charging']['batteryStatus']['value']['currentSOC_pct'])
                        self.range = float(self.data['charging']['batteryStatus']['value']['cruisingRangeElectric_km'])
                        soc_tsZ = self.data['charging']['batteryStatus']['value']['carCapturedTimestamp']
                        soc_tsdtZ = datetime.strptime(soc_tsZ, ts_fmt + "Z")
                    elif self.brand == "skoda":
                        self.soc = int(self.data['primaryEngineRange']['currentSoCInPercent'])
                        self.range = float(self.data['primaryEngineRange']['remainingRangeInKm'])
                        soc_tsZ = self.data['carCapturedTimestamp']
                        soc_tsdtZ = datetime.strptime(soc_tsZ, ts_fmt + ".%fZ")
                    else:
                        raise "Brand " + self.brand + " is not one of vwid, skoda"

                    soc_tsdtL = utc2local(soc_tsdtZ)
                    self.soc_tsX = datetime.timestamp(soc_tsdtL)
                    self.soc_ts = datetime.strftime(soc_tsdtL, ts_fmt)
                except Exception as e:
                    log.exception("soc/range/soc_ts field missing exception: e=" + str(e))
                    self.soc = 0
                    self.range = 0.0
                    self.soc_ts = ""
                    self.soc_tsX = time()

                # decision logic - shall a new refreshToken be stored?
                self.store_refreshToken = False
                self.refreshTokenNew = self.w.tokens['refreshToken']

                if self.refreshTokenOld != initialToken:
                    try:
                        self.expOld, self.expOld_dt = self.su.get_token_expiration(self.refreshTokenOld, date_fmt)
                        self.now = int(time())
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
                elif self.refreshTokenNew != initialToken:
                    self.store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

                if self.store_refreshToken:          # refreshToken needs to be stored in config json
                    try:
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

                return self.soc, self.range, self.soc_ts, self.soc_tsX


def fetch_soc(conf: VWId, vehicle: int) -> Union[int, float, str]:

    # prepare and call async method
    loop = new_event_loop()
    set_event_loop(loop)

    # get soc, range from server
    a = api()
    soc, range, soc_ts, soc_tsX = loop.run_until_complete(a._fetch_soc(conf, vehicle))

    return soc, range, soc_ts, soc_tsX
