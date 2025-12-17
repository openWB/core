#!/usr/bin/env python3

from datetime import datetime
from json import dumps
import logging
from time import mktime, time
from typing import Union
from modules.common.store import RAMDISK_PATH
from modules.vehicles.vwgroup.socutils import socUtils

date_fmt = '%Y-%m-%d %H:%M:%S'
ts_fmt = '%Y-%m-%dT%H:%M:%S'

refreshToken_exp_days = 7    # 7 days before refreshToken expires a new refreshToken shall be stored
initialToken = '1.2.3'


class VwGroup(object):
    def __init__(self, conf, vehicle):
        self.log = logging.getLogger(__name__)
        self.su = socUtils()
        self.user_id = conf.configuration.user_id
        self.password = conf.configuration.password
        self.vin = conf.configuration.vin
        self.refreshToken = conf.configuration.refreshToken
        self.replyFile = 'soc_' + str(conf.type) + '_reply_vh_' + str(vehicle)
        self.accessTokenFile = str(RAMDISK_PATH) + '/soc_' + str(conf.type) + '_accessToken_vh_' + str(vehicle)
        self.accessToken_old = {}
        self.vehicle = vehicle
        self.conf = conf

    # convert utc timestamp to local time
    def utc2local(self, utc):
        epoch = mktime(utc.timetuple())
        offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
        return utc + offset

    # async method, called from sync fetch_soc, required because libvwid/libskoda expect async environment
    async def request_data(self, library) -> Union[int, float, str]:
        library.set_vin(self.vin)
        library.set_credentials(self.user_id, self.password)
        library.set_jobs(['charging'])
        library.tokens = {}
        library.headers = {}

        # initialize refreshToken
        try:
            if self.refreshToken is None:
                self.log.debug("set refreshToken to initial value")
                library.tokens['refreshToken'] = initialToken
            else:
                library.tokens['refreshToken'] = self.refreshToken

        except Exception:
            self.log.debug("refreshToken initialization exception: set refreshToken_old to initial value")
            library.tokens['refreshToken'] = initialToken

        self.refreshTokenOld = library.tokens['refreshToken']   # remember current refreshToken

        # initialize accessToken
        self.accessTokenOld = self.su.read_token_file(self.accessTokenFile)
        if self.accessTokenOld is None:
            self.log.debug('set accessToken to initial value')
            self.accessTokenOld = initialToken
        library.tokens['accessToken'] = self.accessTokenOld     # initialize tokens in vwid
        library.headers['Authorization'] = 'Bearer %s' % library.tokens["accessToken"]

        # get status from VW server
        self.data = await library.get_status()
        if (self.data):
            if self.su.keys_exist(self.data, 'userCapabilities', 'capabilitiesStatus', 'error'):
                self.log.error("Server Error: \n" +
                               dumps(self.data['userCapabilities']['capabilitiesStatus']['error'],
                                     ensure_ascii=False, indent=4))

            if self.su.keys_exist(self.data, 'charging', 'batteryStatus'):
                self.log.debug("batteryStatus: \n" +
                               dumps(self.data['charging']['batteryStatus'],
                                     ensure_ascii=False, indent=4))

            try:
                self.soc = int(self.data['charging']['batteryStatus']['value']['currentSOC_pct'])
                self.range = float(self.data['charging']['batteryStatus']['value']['cruisingRangeElectric_km'])
                soc_tsZ = self.data['charging']['batteryStatus']['value']['carCapturedTimestamp'].replace('ZZ', 'Z')
                soc_tsdtZ = datetime.strptime(soc_tsZ, ts_fmt + "Z")
                soc_tsdtL = self.utc2local(soc_tsdtZ)
                self.soc_tsX = datetime.timestamp(soc_tsdtL)
                self.soc_ts = datetime.strftime(soc_tsdtL, ts_fmt)
            except Exception as e:
                raise Exception("soc/range/soc_ts field missing exception: e=" + str(e))

            # decision logic - shall a new refreshToken be stored?
            self.store_refreshToken = False
            self.refreshTokenNew = library.tokens['refreshToken']

            if self.refreshTokenOld != initialToken:
                try:
                    self.expOld, self.expOld_dt = self.su.get_token_expiration(self.refreshTokenOld, date_fmt)
                    self.now = int(time())
                    expirationThreshold = self.expOld - refreshToken_exp_days * 86400

                    if expirationThreshold < self.now:
                        self.log.debug('RefreshToken: expiration in less than ' +
                                       str(refreshToken_exp_days) + ' days on ' + self.expOld_dt + ', store new token')
                        self.store_refreshToken = True
                except Exception as e:
                    self.log.debug("refreshToken decode exception: e=" + str(e))
                    self.store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

                else:
                    self.log.debug("Old refreshToken expires on " + self.expOld_dt + ", keep it")
            elif self.refreshTokenNew != initialToken:
                self.store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

            if self.store_refreshToken:          # refreshToken needs to be stored in config json
                try:
                    self.expNew, self.expNew_dt = self.su.get_token_expiration(self.refreshTokenNew, date_fmt)
                    self.log.debug("store new refreshToken, expires on " + self.expNew_dt)
                except Exception as e:
                    self.log.debug("new refreshToken decode exception, e=" + str(e))
                    self.log.debug("new refreshToken=" + str(self.refreshTokenNew))

                confDict = self.conf.__dict__
                confDict.pop('name')
                confDict['configuration'] = self.conf.configuration.__dict__
                self.su.write_token_mqtt(
                    "openWB/set/vehicle/" + self.vehicle + "/soc_module/config",
                    self.refreshTokenNew,
                    self.conf.__dict__)

            if (library.tokens['accessToken'] != self.accessTokenOld):  # modified accessToken?
                self.su.write_token_file(self.accessTokenFile, library.tokens['accessToken'])

            return self.soc, self.range, self.soc_ts, self.soc_tsX
