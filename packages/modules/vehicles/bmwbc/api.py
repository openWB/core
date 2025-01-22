#!/usr/bin/env python3

# references:
# https://github.com/bimmerconnected
# https://bimmer-connected.readthedocs.io/en/latest/

import json
import asyncio
import datetime
import logging
from typing import Union

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from bimmer_connected.api.client import MyBMWClientConfiguration
    from bimmer_connected.api.authentication import MyBMWAuthentication
    from bimmer_connected.account import MyBMWAccount
    from bimmer_connected.api.regions import Regions
    from bimmer_connected.utils import MyBMWJSONEncoder

from modules.common.component_state import CarState
from modules.common.store import RAMDISK_PATH
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[4] / "data" / "modules" / "bmwbc"

log = logging.getLogger(__name__)


# ------------ Helper functions -------------------------------------
# initialize store structures when no store is available
def init_store():
    store = {}
    store['refresh_token'] = None
    store['access_token'] = None
    store['expires_at'] = None
    store['gcid'] = None
    store['session_id'] = None
    store['captcha_token'] = None
    return store


# load store from file, if no store file exists initialize store structure
def load_store():
    global storeFile
    try:
        with open(storeFile, 'r', encoding='utf-8') as tf:
            store = json.load(tf)
            if 'refresh_token' not in store:
                store = init_store()
    except FileNotFoundError:
        log.warning("load_store: store file not found, " +
                    "full authentication required")
        store = init_store()
    except Exception as e:
        log.error("init: loading stored data failed, file: " +
                  storeFile + ", error=" + str(e))
        store = init_store()
    return store


# write store file
def write_store(store: dict):
    global storeFile
    with open(storeFile, 'w', encoding='utf-8') as tf:
        json.dump(store, tf, indent=4)


# write a dict as json file - useful for problem analysis
def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout + '.json'
    with open(replyFile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ---------------fetch Function called by core ------------------------------------
async def _fetch_soc(user_id: str, password: str, vin: str, captcha_token: str, vnum: int) -> Union[int, float]:
    global storeFile
    try:
        log.debug("dataPath=" + str(DATA_PATH))
        DATA_PATH.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log.error("init: dataPath creation failed, dataPath: " +
                  str(DATA_PATH) + ", error=" + str(e))
        store = init_store()
        return 0, 0.0
    storeFile = str(DATA_PATH) + '/soc_bmwbc_vh_' + str(vnum) + '.json'

    try:
        # set loggin in httpx to WARNING to prevent unwanted messages
        logging.getLogger("httpx").setLevel(logging.WARNING)

        store = load_store()
        # check for captcha_token in store
        if 'captcha_token' not in store:
            # captcha token not in store - add current captcha_token
            log.info("initialize captcha token in store")
            store['captcha_token'] = captcha_token
            write_store(store)
        else:
            # last used captcha token in store, compare with captcha_token in configuration
            if store['captcha_token'] != captcha_token:
                # invalidate current refresh and access token to force new login
                log.info("new captcha token configured - invalidate stored token set")
                store['expires_at'] = None
                store['access_token'] = None
                store['refresh_token'] = None
                store['session_id'] = None
                store['gcid'] = None
            else:
                log.info("captcha token unchanged")

        if store['expires_at'] is not None:
            # authenticate via refresh and access token
            # user_id, password are provided in case these are required
            log.info("authenticate via current token set")
            expires_at = datetime.datetime.fromisoformat(store['expires_at'])
            auth = MyBMWAuthentication(user_id, password, Regions.REST_OF_WORLD,
                                       refresh_token=store['refresh_token'],
                                       access_token=store['access_token'],
                                       expires_at=expires_at)
        else:
            # no token, authenticate via user_id, password and captcha_token
            log.info("authenticate via userid, password, captcha token")
            auth = MyBMWAuthentication(user_id,
                                       password,
                                       Regions.REST_OF_WORLD,
                                       hcaptcha_token=captcha_token)

        if store['session_id'] is not None:
            auth.session_id = store['session_id']
        if store['gcid'] is not None:
            auth.gcid = store['gcid']

        clconf = MyBMWClientConfiguration(auth)
        # account = MyBMWAccount(user_id, password, Regions.REST_OF_WORLD, config=clconf)
        # user, password and region already set in BMWAuthentication/ClientConfiguration!
        account = MyBMWAccount(None, None, None, config=clconf, hcaptcha_token=captcha_token)

        # get vehicle list - needs to be called async
        await account.get_vehicles()

        # get vehicle data for vin
        vehicle = account.get_vehicle(vin)

        # get json of vehicle data
        resp = json.dumps(vehicle, cls=MyBMWJSONEncoder, indent=4)

        # vehicle data - json to dict
        respd = json.loads(resp)
        state = respd['data']['state']

        # get soc, range, lastUpdated from vehicle data
        soc = int(state['electricChargingState']['chargingLevelPercent'])
        range = float(state['electricChargingState']['range'])
        lastUpdatedAt = state['lastUpdatedAt']

        # save the vehicle data for further analysis if required
        dump_json(respd, '/soc_bmwbc_reply_vehicle_' + str(vnum))

        log.info(" SOC/Range: " + str(soc) + '%/' + str(range) + 'KM@' + lastUpdatedAt)

        # store token and expires_at if changed
        expires_at = datetime.datetime.isoformat(auth.expires_at)
        if store['expires_at'] != expires_at or store['session_id'] != auth.session_id:
            store['refresh_token'] = auth.refresh_token
            store['access_token'] = auth.access_token
            store['captcha_token'] = captcha_token
            store['session_id'] = auth.session_id
            store['gcid'] = auth.gcid
            store['expires_at'] = datetime.datetime.isoformat(auth.expires_at)
            write_store(store)

    except Exception as err:
        log.error("bmwbc.fetch_soc: requestData Error, vnum: " + str(vnum) + f" {err=}, {type(err)=}")
        raise
    return soc, range


# main entry - _fetch needs to be run async
def fetch_soc(user_id: str, password: str, vin: str, captcha_token: str, vnum: int) -> CarState:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    soc, range = loop.run_until_complete(_fetch_soc(user_id, password, vin, captcha_token, vnum))

    return CarState(soc, range)
