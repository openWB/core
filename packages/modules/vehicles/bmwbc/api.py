#!/usr/bin/env python3

# references:
# https://github.com/bimmerconnected
# https://bimmer-connected.readthedocs.io/en/latest/

import json
import asyncio
import datetime
import logging
from typing import Union
from modules.common.component_state import CarState
from modules.common.store import RAMDISK_PATH
from bimmer_connected.api.client import MyBMWClientConfiguration
from bimmer_connected.api.authentication import MyBMWAuthentication
from bimmer_connected.account import MyBMWAccount
from bimmer_connected.api.regions import Regions
from bimmer_connected.utils import MyBMWJSONEncoder


log = logging.getLogger(__name__)


# ------------ Helper functions -------------------------------------
# initialize store structures when no store is available
def init_store():
    store = {}
    store['refresh_token'] = None
    store['access_token'] = None
    store['expires_at'] = None
    return store


# load store from file, if no store file exists initialize store structure
def load_store():
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
    with open(storeFile, 'w', encoding='utf-8') as tf:
        json.dump(store, tf, indent=4)


# write a dict as json file - useful for problem analysis
def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout + '.json'
    with open(replyFile, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ---------------fetch Function called by core ------------------------------------
async def _fetch_soc(user_id: str, password: str, vin: str, vnum: int) -> Union[int, float]:
    global storeFile
    storeFile = str(RAMDISK_PATH) + '/soc_bmwbc_vh_' + str(vnum) + '.json'

    try:
        # set loggin in httpx to WARNING to prevent unwanted messages
        logging.getLogger("httpx").setLevel(logging.WARNING)

        store = load_store()
        if store['expires_at'] is not None:
            # authenticate via refresh and access token
            # user_id, password are provided in case these are required
            expires_at = datetime.datetime.fromisoformat(store['expires_at'])
            auth = MyBMWAuthentication(user_id, password, Regions.REST_OF_WORLD,
                                       refresh_token=store['refresh_token'],
                                       access_token=store['access_token'],
                                       expires_at=expires_at)
        else:
            # no token, authenticate via user_id and password only
            auth = MyBMWAuthentication(user_id, password, Regions.REST_OF_WORLD)

        clconf = MyBMWClientConfiguration(auth)
        # account = MyBMWAccount(user_id, password, Regions.REST_OF_WORLD, config=clconf)
        # user, password and region already set in BMWAuthentication/ClientConfiguration!
        account = MyBMWAccount(None, None, None, config=clconf)

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
        if store['expires_at'] != expires_at:
            store['refresh_token'] = auth.refresh_token
            store['access_token'] = auth.access_token
            store['expires_at'] = datetime.datetime.isoformat(auth.expires_at)
            write_store(store)

    except Exception as err:
        log.error("bmwbc.fetch_soc: requestData Error, vnum: " + str(vnum) + f" {err=}, {type(err)=}")
        raise
    return soc, range


# main entry - _fetch needs to be run async
def fetch_soc(user_id: str, password: str, vin: str, vnum: int) -> CarState:

    # prepare and call async method
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # get soc, range from server
    soc, range = loop.run_until_complete(_fetch_soc(user_id, password, vin, vnum))

    return CarState(soc, range)
