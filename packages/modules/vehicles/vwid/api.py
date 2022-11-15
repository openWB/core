#!/usr/bin/env python3

import logging
from typing import Tuple
from modules.vehicles.vwid import libvwid
import os
import aiohttp
import asyncio
import json
import pickle
import getpass
from modules.common.store import RAMDISK_PATH

log = logging.getLogger("soc."+__name__)

# async method, called from sync fetch_soc, required because libvwid expects  async enviroment


async def _fetch_soc(user_id: str, password: str, vin: str, vehicle: int) -> Tuple[int, float]:
    # log.debug("vwid:_fetch_soc, user_id="+user_id)
    # log.debug("vwid:_fetch_soc, password=" + password)
    # log.debug("vwid:_fetch_soc, vin="+vin)
    # log.debug("vwid:_fetch_soc, vehicle="+vehicle)

    replyFile = str(RAMDISK_PATH) + '/soc_vwid_reply_vehicle_' + str(vehicle)
    tokensFile = str(RAMDISK_PATH) + '/soc_vwid_tokens_vehicle_' + str(vehicle)

    async with aiohttp.ClientSession() as session:
        w = libvwid.vwid(session)
        w.set_vin(vin)
        w.set_credentials(user_id, password)

        try:
            tf = open(tokensFile, "rb")           # try to open tokens file
            w.tokens = pickle.load(tf)            # initialize tokens in vwid
            tokens_old = pickle.dumps(w.tokens)   # remember current tokens
            w.headers['Authorization'] = 'Bearer %s' % w.tokens["accessToken"]
            tf.close()
        except Exception as e:
            log.debug("vehicle " + str(vehicle) + ", tokens initialization exception: e=" + str(e))
            log.debug("vehicle " + str(vehicle) + ", tokens initialization exception: set tokens_old to initial value")
            tokens_old = bytearray(1)             # if no old token found set tokens_old to dummy value

        data = await w.get_status()
        if (data):
            soc = (data['data']['batteryStatus']['currentSOC_pct'])
            range = float(data['data']['batteryStatus']['cruisingRangeElectric_km'])
            try:
                f = open(replyFile, 'w', encoding='utf-8')
            except Exception as e:
                log.debug("vehicle " + str(vehicle) +
                          ", replyFile open exception: e=" + str(e) + "user: " + getpass.getuser())
                log.debug("vehicle " + str(vehicle) + ", replyFile open Exception, remove existing file")
                os.system("sudo rm " + replyFile)
                f = open(replyFile, 'w', encoding='utf-8')
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.close()
            try:
                os.chmod(replyFile, 0o777)
            except Exception as e:
                log.debug("vehicle " + str(vehicle) + ", chmod replyFile exception, e=" + str(e))
                log.debug("vehicle " + str(vehicle) + ", use sudo, user: " + getpass.getuser())
                os.system("sudo chmod 0777 " + replyFile)

            tokens_new = pickle.dumps(w.tokens)
            if (tokens_new != tokens_old):    # check for modified tokens
                log.debug("vehicle " + str(vehicle) + ", tokens_new != tokens_old, rewrite tokens file")
                tf = open(tokensFile, "wb")
                pickle.dump(w.tokens, tf)     # write tokens file
                tf.close()
                try:
                    os.chmod(tokensFile, 0o777)
                except Exception as e:
                    log.debug("vehicle " +
                              str(vehicle) + ", chmod tokensFile exception, use sudo, e=" +
                              str(e) + "user: " + getpass.getuser())
                    os.system("sudo chmod 0777 " + tokensFile)
            # log.debug("vwid.api._fetch_soc return: soc=" + str(soc) + "range=" + str(range))
            return soc, range


def fetch_soc(user_id: str, password: str, vin: str, vehicle: int) -> Tuple[int, float]:
    # log.debug("vwid:fetch_soc, user_id=" + user_id)
    # log.debug("vwid:fetch_soc, password=" + password)
    # log.debug("vwid:fetch_soc, vin=" + vin)
    # log.debug("vwid: fetch_soc, vehicle=" + vehicle)

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    soc, range = loop.run_until_complete(_fetch_soc(user_id, password, vin, vehicle))
    # log.debug("vwid.api.fetch_soc vehicle " + vehicle + ", return: soc=" + str(soc) + ", range=" + str(range))
    return soc, range
