#!/usr/bin/env python3

import logging
from typing import Union
from modules.vehicles.vwid import libvwid
import os
import aiohttp
import asyncio
import json
import datetime
import time
import jwt
from modules.common.store import RAMDISK_PATH
from helpermodules.pub import Pub

date_fmt = '%Y-%m-%d %H:%M:%S'
refreshToken_exp_days = 7    # 7 days before refreshToken expires a new refreshToken shall be stored

log = logging.getLogger("soc."+__name__)


def dump_json(data: dict, fout: str):
    if log.getEffectiveLevel() < 20:
        jsonFile = str(RAMDISK_PATH) + '/' + fout
        try:
            f = open(jsonFile, 'w', encoding='utf-8')
        except Exception as e:
            log.debug("vwid.dump_json: chmod File" + jsonFile + ", exception, e=" + str(e))
            os.system("sudo rm " + jsonFile)
            f = open(jsonFile, 'w', encoding='utf-8')
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.close()

# async method, called from sync fetch_soc, required because libvwid expects  async enviroment


async def _fetch_soc(user_id: str, password: str, vin: str, refreshToken: str, vehicle: int) -> Union[int, float]:
    replyFile = 'soc_vwid_reply_vh_' + str(vehicle)
    accessTokenFile = str(RAMDISK_PATH) + '/soc_vwid_accessToken_vehicle_' + str(vehicle)
    accessToken_old = {}

    async with aiohttp.ClientSession() as session:
        w = libvwid.vwid(session)
        w.set_vin(vin)
        w.set_credentials(user_id, password)
        w.tokens = {}
        w.headers = {}

        try:
            if refreshToken is None:
                log.debug("set refreshToken to initial value")
                w.tokens['refreshToken'] = '1.2.3'
            else:
                w.tokens['refreshToken'] = refreshToken

        except Exception as e:
            log.debug("vehicle " + vehicle + ", refreshToken initialization exception: e=" + str(e))
            log.debug("vehicle " + vehicle +
                      ", refreshToken initialization exception: set refreshToken_old to initial value")
            w.tokens['refreshToken'] = "1.2.3"
        refreshTokenOld = w.tokens['refreshToken']                  # remember current refreshToken

        try:
            tf = open(accessTokenFile, "r")           # try to open accessToken file
            w.tokens['accessToken'] = tf.read()            # initialize tokens in vwid
            accessToken_old = w.tokens['accessToken']      # remember current accessToken
            w.headers['Authorization'] = 'Bearer %s' % w.tokens["accessToken"]
            tf.close()
        except Exception as e:
            log.debug("vehicle " + vehicle +
                      ', accessToken initialization exception ' + str(e) + ': set accessToken to initial value')
            accessToken_old = "1.2.3"  # if no old token found set accessToken_old to dummy value
            w.tokens['accessToken'] = "1.2.3"  # if no old token found set accessToken_old to dummy value
            w.headers['Authorization'] = 'Bearer %s' % w.tokens["accessToken"]

        data = await w.get_status()
        if (data):
            soc = (data['data']['batteryStatus']['currentSOC_pct'])
            range = float(data['data']['batteryStatus']['cruisingRangeElectric_km'])
            dump_json(data, replyFile)

            # decision logic - shall a new refreshToken be stored?
            store_refreshToken = False
            refreshToken_new = w.tokens['refreshToken']
            if refreshTokenOld != "1.2.3":
                try:
                    refreshTokenOld_decoded = jwt.decode(refreshTokenOld, options={"verify_signature": False})
                    expOld = refreshTokenOld_decoded['exp']
                    now = int(time.time())
                    expirationThreshold = expOld - refreshToken_exp_days * 86400
                    expOld_dt = datetime.datetime.fromtimestamp(expOld).strftime(date_fmt)

                    # start debugging section: the _dt variables are for debugging
                    # now_dt = datetime.datetime.fromtimestamp(now).strftime(date_fmt)
                    # expirationThreshold_dt = datetime.datetime.fromtimestamp(expirationThreshold).strftime(date_fmt)
                    # log.debug("vehicle " + vehicle + ": old expiration date: " + expOld_dt)
                    # log.debug("vehicle " + vehicle + ": current date       : " + now_dt)
                    # log.debug("vehicle " + vehicle + ": expirationThreshold: " + expirationThreshold_dt)
                    # end of debugging section

                    if expirationThreshold < now:
                        log.debug("vehicle " + vehicle +
                                  ': expiration in less than ' +
                                  str(refreshToken_exp_days) + ' days on ' + expOld_dt + ', store new token')
                        store_refreshToken = True
                except Exception as e:
                    log.debug("vehicle " + vehicle + ", refreshToken decode exception: e=" + str(e))
                    store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

                else:
                    log.debug("vehicle " + vehicle + ": expiration in more than " +
                              str(refreshToken_exp_days) + ' days on ' + expOld_dt + ', keep refreshToken')
            else:
                store_refreshToken = True   # no old refreshToken, store new refreshToken anyway

            if store_refreshToken:          # refreshToken needs to be stored in config json
                log.debug("vehicle " + vehicle + ": save new refreshToken to config")
                config = {}
                config['type'] = "vwid"
                config['configuration'] = {}
                config['configuration']['user_id'] = user_id
                config['configuration']['password'] = password
                config['configuration']['vin'] = vin
                config['configuration']['refreshToken'] = refreshToken_new
                Pub().pub("openWB/set/vehicle/" + vehicle + "/soc_module/config", config)

            accessToken_new = w.tokens['accessToken']
            if (accessToken_new != accessToken_old):    # check for modified access token
                log.debug("vehicle " + vehicle + ", accessToken mismatch, rewrite token file")
                tf = open(accessTokenFile, "w")
                tf.write(w.tokens['accessToken'])     # write accessToken file
                tf.close()

            return soc, range


def fetch_soc(user_id: str, password: str, vin: str, refreshToken: str, vehicle: int) -> Union[int, float]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    soc, range = loop.run_until_complete(_fetch_soc(user_id, password, vin, refreshToken, vehicle))

    return soc, range
