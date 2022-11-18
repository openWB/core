#!/usr/bin/env python3

import logging
from typing import Union
from modules.vehicles.vwid import libvwid
import os
import aiohttp
import asyncio
import json
import pickle
import binascii
from modules.common.store import RAMDISK_PATH
from helpermodules.pub import Pub

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
    refreshToken_old = {}
    accessToken_old = {}

    async with aiohttp.ClientSession() as session:
        w = libvwid.vwid(session)
        w.set_vin(vin)
        w.set_credentials(user_id, password)
        w.tokens = {}
        w.headers = {}

        try:
            if refreshToken is None:
                w.tokens['refreshToken'] = bytearray(1)
            else:
                refreshTokenB = binascii.unhexlify(refreshToken)
                w.tokens['refreshToken'] = pickle.loads(refreshTokenB)

            refreshToken_old = pickle.dumps(w.tokens['refreshToken'])   # remember current refreshToken
        except Exception as e:
            log.debug("vehicle " + vehicle + ", refreshToken initialization exception: e=" + str(e))
            log.debug("vehicle " + vehicle +
                      ", refreshToken initialization exception: set refreshToken_old to initial value")
            refreshToken_old['refreshToken'] = bytearray(1)  # if no old token found set refreshToken_old to dummy value
            w.tokens['refreshToken'] = bytearray(1)

        try:
            tf = open(accessTokenFile, "rb")           # try to open accessToken file
            w.tokens['accessToken'] = pickle.load(tf)            # initialize tokens in vwid
            accessToken_old = pickle.dumps(w.tokens['accessToken'])   # remember current accessToken
            w.headers['Authorization'] = 'Bearer %s' % w.tokens["accessToken"]
            tf.close()
        except Exception as e:
            log.debug("vehicle " + vehicle + ", accessToken initialization exception: e=" + str(e))
            log.debug("vehicle " + vehicle +
                      ", accessToken initialization exception: set accessToken_old to initial value")
            accessToken_old['accessToken'] = bytearray(1)  # if no old token found set accessToken_old to dummy value
            w.tokens['accessToken'] = bytearray(1)  # if no old token found set accessToken_old to dummy value
            w.headers['Authorization'] = 'Bearer %s' % w.tokens["accessToken"]

        data = await w.get_status()
        if (data):
            soc = (data['data']['batteryStatus']['currentSOC_pct'])
            range = float(data['data']['batteryStatus']['cruisingRangeElectric_km'])
            dump_json(data, replyFile)

            refreshToken_new = pickle.dumps(w.tokens['refreshToken'])
            if (refreshToken_new != refreshToken_old):    # check for modified request token
                log.debug("vehicle " + vehicle + ", refreshToken mismatch, save new refreshToken to config")
                config = {}
                config['type'] = "vwid"
                config['configuration'] = {}
                config['configuration']['user_id'] = user_id
                config['configuration']['password'] = password
                config['configuration']['vin'] = vin
                config['configuration']['refreshToken'] = str(binascii.hexlify(refreshToken_new), 'ascii')
                Pub().pub("openWB/set/vehicle/" + vehicle + "/soc_module/config", config)

            accessToken_new = pickle.dumps(w.tokens['accessToken'])
            if (accessToken_new != accessToken_old):    # check for modified access token
                log.debug("vehicle " + vehicle + ", accessToken mismatch, rewrite token file")
                tf = open(accessTokenFile, "wb")
                pickle.dump(w.tokens['accessToken'], tf)     # write accessToken file
                tf.close()

            return soc, range


def fetch_soc(user_id: str, password: str, vin: str, refreshToken: str, vehicle: int) -> Union[int, float]:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    soc, range = loop.run_until_complete(_fetch_soc(user_id, password, vin, refreshToken, vehicle))
    # log.debug("vwid.api.fetch_soc vehicle " + vehicle + ", return: soc=" + str(soc) + ", range=" + str(range))
    return soc, range
