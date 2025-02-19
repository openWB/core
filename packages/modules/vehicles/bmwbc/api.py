#!/usr/bin/env python3

# references:
# https://github.com/bimmerconnected
# https://bimmer-connected.readthedocs.io/en/latest/

from typing import Union
from logging import getLogger, WARNING
from json import load, dump, loads, dumps
from asyncio import new_event_loop, set_event_loop
from datetime import datetime
from copy import deepcopy
from threading import Lock

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
ts_fmt = '%Y-%m-%dT%H:%M:%S'
dt_fmt = '%Y-%m-%d %H:%M:%S'
api = None

log = getLogger(__name__)


# ------------ Helper functions -------------------------------------
# send store content n debug level to soc log
def log_store(store: dict, txt: str):
    st = deepcopy(store)            # create a copy of the store
    st['rt'] = st['refresh_token']  # copy key to avoid REDACTED
    st['at'] = st['access_token']   # copy key to avoid REDACTED
    log.info("store file action:" + txt)
    log.debug(txt + ":\n" + dumps(st, indent=4))


# initialize store structures when no store is available
def init_store():
    store = {}
    store['refresh_token'] = None
    store['access_token'] = None
    store['expires_at'] = None
    store['gcid'] = None
    store['session_id'] = None
    store['captcha_token'] = None
    log_store(store, "store initialized")
    return store


# load store from file, if no store file exists initialize store structure
def load_store():
    global storeFile
    try:
        with open(storeFile, 'r', encoding='utf-8') as tf:
            store = load(tf)
            log_store(store, "store loaded")
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
        dump(store, tf, indent=4)
    log_store(store, "store written")


# write a dict as json file - useful for problem analysis
def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout + '.json'
    with open(replyFile, 'w', encoding='utf-8') as f:
        dump(data, f, ensure_ascii=False, indent=4)


# Exception class - used in raise
class RequestFailed(Exception):
    def __init__(self, m):
        self.message = m

    def __str__(self):
        return self.message


class Api:
    # initialize class variables
    _auth = None
    _clconf = None
    _account = None
    _store = None

    # --------------- async fetch Function called by fetch_soc ------------------------------------
    async def _fetch_soc(self,
                         user_id: str,
                         password: str,
                         vin: str,
                         captcha_token: str,
                         vnum: int) -> Union[int, float]:

        global storeFile

        # make sure teh patch for the store fie exists
        try:
            log.debug("dataPath=" + str(DATA_PATH))
            DATA_PATH.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.error("init: dataPath creation failed, dataPath: " +
                      str(DATA_PATH) + ", error=" + str(e))
            if self._store is None:
                self._store = init_store()
            return 0, 0.0

        storeFile = str(DATA_PATH) + '/soc_bmwbc_vh_' + str(vnum) + '.json'

        try:
            # set logging in httpx to WARNING to prevent unwanted log messages from bimmeer connected
            getLogger("httpx").setLevel(WARNING)

            if self._store is None:
                self._store = load_store()

            # check for captcha_token in store
            if 'captcha_token' not in self._store:
                # captcha token not in self._store - add current captcha_token
                log.debug("initialize captcha token in store")
                self._store['captcha_token'] = captcha_token
                write_store(self._store)
            else:
                # last used captcha token in store, compare with captcha_token in configuration
                if self._store['captcha_token'] != captcha_token:
                    # invalidate current refresh and access token to force new login
                    log.debug("new captcha token configured - invalidate stored token set")
                    self._store['expires_at'] = None
                    self._store['access_token'] = None
                    self._store['refresh_token'] = None
                    self._store['session_id'] = None
                    self._store['gcid'] = None
                else:
                    log.debug("captcha token unchanged")

            if self._store['expires_at'] is not None and \
               self._store['refresh_token'] is not None and \
               self._store['access_token'] is not None:
                # authenticate via refresh and access token
                # user_id, password are provided in case these are required
                log.info("authenticate via current token set")
                expires_at = datetime.fromisoformat(self._store['expires_at'])
                if self._auth is None:
                    self._auth = MyBMWAuthentication(user_id, password, Regions.REST_OF_WORLD,
                                                     refresh_token=self._store['refresh_token'],
                                                     access_token=self._store['access_token'],
                                                     expires_at=expires_at)
            else:
                # no token, authenticate via user_id, password and captcha_token
                log.info("authenticate via userid, password, captcha token")
                if self._auth is None:
                    log.debug("# Create _auth instance")
                    self._auth = MyBMWAuthentication(user_id,
                                                     password,
                                                     Regions.REST_OF_WORLD,
                                                     hcaptcha_token=captcha_token)
                else:
                    log.debug("# Reuse _auth instance")

            # set sessuin_id and gcid in _auth to store values
            if self._store['session_id'] is not None:
                self._auth.session_id = self._store['session_id']
            if self._store['gcid'] is not None:
                self._auth.gcid = self._store['gcid']

            # instantiate client configuration object is not existent yet
            if self._clconf is None:
                log.debug("# Create _clconf instance")
                self._clconf = MyBMWClientConfiguration(self._auth)
            else:
                log.debug("# Reuse _clconf instance")

            # instantiate account object of not existent yet
            if self._account is None:
                log.debug("# Create _account instance")
                # user, password and region already set in BMWAuthentication/ClientConfiguration!
                self._account = MyBMWAccount(None, None, None, config=self._clconf, hcaptcha_token=captcha_token)
                self._account.set_refresh_token(refresh_token=self._store['refresh_token'],
                                                gcid=self._store['gcid'],
                                                access_token=self._store['access_token'],
                                                session_id=self._store['session_id'])
            else:
                log.debug("# Reuse _account instance")

            # experimental: login  when expires_at is reached to force token refresh
            expires_at = datetime.fromisoformat(self._store['expires_at'])
            nowdt = datetime.now(expires_at.tzinfo)

            if nowdt > expires_at:
                log.info("# Proactive login to force refresh token before get_vehicles")
                log.info("# before proactive login:" + str(self._auth.expires_at) +
                         "/" + self._auth.refresh_token)
                await self._auth.login()
                log.info("# after  proactive login:" + str(self._auth.expires_at) +
                         "/" + self._auth.refresh_token)

            # get vehicle list - needs to be called async
            await self._account.get_vehicles()

            # get vehicle data for vin
            vehicle = self._account.get_vehicle(vin)

            # get json of vehicle data
            resp = dumps(vehicle, cls=MyBMWJSONEncoder, indent=4)

            # vehicle data - json to dict
            respd = loads(resp)
            state = respd['data']['state']

            # get soc, range, lastUpdated from vehicle data
            soc = int(state['electricChargingState']['chargingLevelPercent'])
            range = float(state['electricChargingState']['range'])
            lastUpdatedAt = state['lastUpdatedAt']
            # convert lastUpdatedAt to soc_timestamp
            soc_tsdtZ = datetime.strptime(lastUpdatedAt, ts_fmt + "Z")
            soc_tsX = datetime.timestamp(soc_tsdtZ)

            # save the vehicle data for further analysis if required
            dump_json(respd, '/soc_bmwbc_reply_vehicle_' + str(vnum))

            log.info(" SOC/Range: " + str(soc) + '%/' + str(range) + 'KM@' + lastUpdatedAt)

            # store token and expires_at if changed
            expires_at = datetime.isoformat(self._auth.expires_at)
            if self._store['expires_at'] != expires_at or \
               self._store['session_id'] != self._auth.session_id or \
               self._store['gcid'] != self._auth.gcid or \
               self._store['access_token'] != self._auth.access_token or \
               self._store['refresh_token'] != self._auth.refresh_token:
                self._store['refresh_token'] = self._auth.refresh_token
                self._store['access_token'] = self._auth.access_token
                self._store['captcha_token'] = captcha_token
                self._store['session_id'] = self._auth.session_id
                self._store['gcid'] = self._auth.gcid
                self._store['expires_at'] = datetime.isoformat(self._auth.expires_at)
                write_store(self._store)
                log.debug("# after  write_store :" + str(self._auth.expires_at) +
                          "/" + self._auth.refresh_token)

        except Exception as err:
            log.error("bmwbc.fetch_soc: requestData Error, vnum: " + str(vnum) + f" {err=}, {type(err)=}")
            self._auth = None
            self._clconf = None
            self._account = None
            raise RequestFailed("SoC Request failed:\n" + str(err))
        return soc, range, soc_tsX


# main entry - _fetch needs to be run async
def fetch_soc(user_id: str, password: str, vin: str, captcha_token: str, vnum: int) -> CarState:
    global api
    _lock = Lock()

    # prepare and call async method
    loop = new_event_loop()
    set_event_loop(loop)

    # instantiate only 1 instance of Api
    if api is None:
        with _lock:
            if api is None:
                api = Api()
                log.debug("# instantiate Api as api")
            else:
                log.debug("# reuse instance Api as api (L)")
    else:
        log.debug("# reuse instance Api as api")

    # get soc, range, soc_timestamp from server
    soc, range, soc_tsX = loop.run_until_complete(api._fetch_soc(user_id, password, vin, captcha_token, vnum))

    return CarState(soc=soc, range=range, soc_timestamp=soc_tsX)
