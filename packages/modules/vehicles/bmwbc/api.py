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
# from uuid import uuid4
import os.path
import shutil
import time

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from bimmer_connected.api.client import MyBMWClientConfiguration
    from bimmer_connected.api.authentication import MyBMWAuthentication
    from bimmer_connected.account import MyBMWAccount
    from bimmer_connected.api.regions import Regions
    from bimmer_connected.utils import MyBMWJSONEncoder
    from bimmer_connected.models import MyBMWAPIError

from modules.common.component_state import CarState
from modules.common.store import RAMDISK_PATH
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[4] / "data" / "modules" / "bmwbc"
ts_fmt = '%Y-%m-%dT%H:%M:%S'
dt_fmt = '%Y-%m-%d %H:%M:%S'
storeFilePrefix = '/soc_bmwbc_'
storeFileTypeVehicle = 'vh_'
storeFileTypeUserid = 'usr_'
jsonFilePostfix = '.json'
replyFilePrefix = '/soc_bmwbc_reply_vehicle_'

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
def load_store(user_id: str, vehicle_id: str) -> dict:
    try:
        # check for user_id storefile
        # if not check for vehicle_id storefile
        storeFileUserid = str(DATA_PATH) + storeFilePrefix + storeFileTypeUserid + user_id + jsonFilePostfix
        storeFileVehicle = str(DATA_PATH) + storeFilePrefix + storeFileTypeVehicle + vehicle_id + jsonFilePostfix
        if os.path.isfile(storeFileUserid):
            log.debug("load_store: storeFileUserid found")
            storeFile = storeFileUserid
        elif os.path.isfile(storeFileVehicle):
            log.debug("load_store: storeFileUserid not found, storeFileVehicle found")
            shutil.copy(storeFileVehicle, storeFileUserid)
            storeFile = storeFileUserid
        else:
            log.warning("no store file found, init store")
            store = init_store()
            return store
    except Exception as e:
        log.error("init: loading stored data failed, file: " +
                  storeFile + ", error=" + str(e))
        store = init_store()
        return store

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
def write_store(store: dict, user_id: str, vehicle_id: str):
    storeFile = str(DATA_PATH) + storeFilePrefix + storeFileTypeUserid + user_id + jsonFilePostfix
    with open(storeFile, 'w', encoding='utf-8') as tf:
        dump(store, tf, indent=4)
    log_store(store, "store written")


# write a dict as json file - useful for problem analysis
def dump_json(data: dict, fout: str):
    replyFile = str(RAMDISK_PATH) + fout + jsonFilePostfix
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
    _instance = None
    _store = {}
    _auth = {}
    _clconf = {}
    _account = {}
    _last_reload = {}
    _primary_vehicle_id = {}
    _lock = Lock()

    def __new__(self, *args, **kwargs):
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    log.debug('#  Instantiate api object')
                    self._instance = object.__new__(self)
                    self.user_id = None
                    self.password = None
                else:
                    log.debug('#  Reuse api _instance')
        else:
            log.debug('#  Reuse api _instance')
        return self._instance

    # --------------- async fetch Function called by fetch_soc ------------------------------------
    async def _fetch_soc(self,
                         user_id: str,
                         password: str,
                         vin: str,
                         captcha_token: str,
                         vehicle_id: str) -> Union[int, float]:

        # make sure the path for the store fie exists
        try:
            log.debug("dataPath=" + str(DATA_PATH))
            DATA_PATH.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.error("init: dataPath creation failed, dataPath: " +
                      str(DATA_PATH) + ", error=" + str(e))
            if user_id not in self._store:
                self._store[user_id] = init_store()
            return 0, 0.0, 0

        # if self._storeFile is None:
        if user_id not in self._primary_vehicle_id:
            if captcha_token != "SECONDARY":
                self._primary_vehicle_id[user_id] = vehicle_id
            else:
                log.warning("sequence problem: secondary starts without preceding primary")
                raise RequestFailed("sequence problem: secondary starts without preceding primary")

        try:
            # initialize return values in case we get into trouble
            soc = 0
            range = 0.0
            soc_tsX = 0.0

            if captcha_token != "SECONDARY":
                self._mode = "PRIMARY  "
                # set logging in httpx to WARNING to prevent unwanted log messages from bimmeer connected
                getLogger("httpx").setLevel(WARNING)

                if user_id not in self._store:
                    self._store[user_id] = load_store(user_id, self._primary_vehicle_id[user_id])

                # check for captcha_token in store
                if 'captcha_token' not in self._store[user_id]:
                    # captcha token not in self._store - add current captcha_token
                    log.debug("initialize captcha token in store")
                    self._store[user_id]['captcha_token'] = captcha_token
                    write_store(self._store[user_id], user_id, self._primary_vehicle_id[user_id])
                else:
                    # last used captcha token in store, compare with captcha_token in configuration
                    if self._store[user_id]['captcha_token'] != captcha_token:
                        # invalidate current refresh and access token to force new login
                        log.debug("new captcha token configured - invalidate stored token set")
                        self._new_captcha = True
                        self._store[user_id]['expires_at'] = None
                        self._store[user_id]['access_token'] = None
                        self._store[user_id]['refresh_token'] = None
                        self._store[user_id]['session_id'] = None
                        self._store[user_id]['gcid'] = None
                    else:
                        log.debug("captcha token unchanged")
                        self._new_captcha = False

                if user_id not in self._auth:
                    if self._store[user_id]['expires_at'] is not None and \
                       self._store[user_id]['refresh_token'] is not None and \
                       self._store[user_id]['access_token'] is not None:
                        # authenticate via refresh and access token
                        # user_id, password are provided in case these are required
                        log.info("authenticate via current token set")
                        expires_at = datetime.fromisoformat(self._store[user_id]['expires_at'])
                        self._auth[user_id] = MyBMWAuthentication(
                                                                  user_id,
                                                                  password,
                                                                  Regions.REST_OF_WORLD,
                                                                  refresh_token=self._store[user_id]['refresh_token'],
                                                                  access_token=self._store[user_id]['access_token'],
                                                                  expires_at=expires_at,
                                                                  hcaptcha_token=captcha_token)
                    else:
                        # no token, authenticate via user_id, password and captcha_token
                        log.info("authenticate via userid, password, captcha token")
                        log.debug("# Create _auth instance")
                        self._auth[user_id] = MyBMWAuthentication(user_id,
                                                                  password,
                                                                  Regions.REST_OF_WORLD,
                                                                  hcaptcha_token=captcha_token)
                else:
                    log.debug("# Reuse _auth instance")

                # set session_id and gcid in _auth to store values
                if self._store[user_id]['session_id'] is not None:
                    self._auth[user_id].session_id = self._store[user_id]['session_id']
                if self._store[user_id]['gcid'] is not None:
                    self._auth[user_id].gcid = self._store[user_id]['gcid']

                # instantiate client configuration object is not existent yet
                if user_id not in self._clconf:
                    log.debug("# Create _clconf instance")
                    self._clconf[user_id] = MyBMWClientConfiguration(self._auth[user_id])
                else:
                    log.debug("# Reuse _clconf instance")

                # instantiate account object if not existent yet
                if user_id not in self._account:
                    log.debug("# Create _account instance")
                    # user, password and region already set in BMWAuthentication/ClientConfiguration!
                    self._account[user_id] = MyBMWAccount(None, None, None,
                                                          config=self._clconf[user_id],
                                                          hcaptcha_token=captcha_token)
                    self._account[user_id].set_refresh_token(refresh_token=self._store[user_id]['refresh_token'],
                                                             gcid=self._store[user_id]['gcid'],
                                                             access_token=self._store[user_id]['access_token'],
                                                             session_id=self._store[user_id]['session_id'])
                else:
                    log.debug("# Reuse _account instance")
            else:
                self._mode = "SECONDARY"

            # get vehicle list - if last reload is more than 5 min ago
            self._now = datetime.timestamp(datetime.now())
            if user_id not in self._last_reload:
                self._last_reload[user_id] = 0
            if self._now > self._last_reload[user_id] + 5 * 60:
                # self._auth[user_id].session_id = str(uuid4())  # experimental to avoid error 408: reset session_id
                # experimental: login  when expires_at is reached to force token refresh
                if self._store[user_id]['expires_at'] is not None:
                    expires_at = datetime.fromisoformat(self._store[user_id]['expires_at'])
                    nowdt = datetime.now(expires_at.tzinfo)

                    if nowdt > expires_at:
                        log.debug("# Proactive login to force refresh token before get_vehicles")
                        log.debug("# before proactive login:" + str(self._auth[user_id].expires_at) +
                                  "/" + self._auth[user_id].refresh_token)
                        await self._auth[user_id].login()
                        log.debug("# after  proactive login:" + str(self._auth[user_id].expires_at) +
                                  "/" + self._auth[user_id].refresh_token)

                # get vehicle list - needs to be called async
                _loop = 5  # 5 retries
                while _loop > 0:
                    _err = 0
                    log.info(self._mode + ": reload vehicles data, _loop=" + str(_loop))
                    try:
                        await self._account[user_id].get_vehicles()
                    except MyBMWAPIError as err:
                        _err = -1
                        if 'Internal Server Error' in str(err):
                            log.info(self._mode + ": get_vehicles : Internal Server Error (500)")
                            _err = 500
                        elif 'Request Timeout' in str(err):
                            log.info(self._mode + ": get_vehicles : Request Timeout (408)")
                            _err = 408
                        else:
                            log.info(self._mode + ": get_vehicles err=" + str(err))
                        log.info(self._mode + ": get_vehicles : MyBMWAPIError, _loop/_err=" +
                                 str(_loop) + "/" + str(_err))
                        time.sleep(10)  # sleep for 10 secs before token refresh
                        log.info("# before except login:" + str(self._auth[user_id].expires_at))
                        # refresh token
                        await self._auth[user_id].login()
                        log.info("# after  except login:" + str(self._auth[user_id].expires_at))
                        # await self._account[user_id].get_vehicles()
                        time.sleep(5)  # sleep for 5 secs after token refresh
                        _loop = _loop - 1
                    except Exception as err:
                        log.error("bmwbc.fetch_soc: get_vehicles Error, vehicle_id: " +
                                  vehicle_id + f" {err=}, {type(err)=}")
                        raise err
                    self._last_reload[user_id] = datetime.timestamp(datetime.now())
                    if _err == 0:
                        _loop = 0

            # get vehicle data for vin
            vehicle = self._account[user_id].get_vehicle(vin)

            # get json of vehicle data
            resp = dumps(vehicle, cls=MyBMWJSONEncoder, indent=4)

            # vehicle data - json to dict
            respd = loads(resp)
            state = respd['data']['state']

            # get soc, range, lastUpdated from vehicle data
            soc = int(state['electricChargingState']['chargingLevelPercent'])
            range = float(state['electricChargingState']['range'])
            lastUpdatedAt = state['lastUpdatedAt']
            if self._new_captcha:
                # after new captcha use system timestamp
                # soc_tsX = datetime.timestamp(datetime.now())
                # after new captcha use timestamp 0 (19700101)
                soc_tsX = 0
            else:
                # convert lastUpdatedAt to soc_timestamp
                soc_tsdtZ = datetime.strptime(lastUpdatedAt, ts_fmt + "Z")
                soc_tsX = datetime.timestamp(soc_tsdtZ)

            # save the vehicle data for further analysis if required
            dump_json(respd, replyFilePrefix + vehicle_id)

            log.info(self._mode + " SOC/Range: " + str(soc) + '%/' + str(range) + 'KM@' + lastUpdatedAt)

            # store token and expires_at if changed
            expires_at = datetime.isoformat(self._auth[user_id].expires_at)
            if self._store[user_id]['expires_at'] != expires_at or \
               self._store[user_id]['session_id'] != self._auth[user_id].session_id or \
               self._store[user_id]['gcid'] != self._auth[user_id].gcid or \
               self._store[user_id]['access_token'] != self._auth[user_id].access_token or \
               self._store[user_id]['refresh_token'] != self._auth[user_id].refresh_token:
                self._store[user_id]['refresh_token'] = self._auth[user_id].refresh_token
                self._store[user_id]['access_token'] = self._auth[user_id].access_token
                if captcha_token != "SECONDARY":
                    self._store[user_id]['captcha_token'] = captcha_token
                self._store[user_id]['session_id'] = self._auth[user_id].session_id
                self._store[user_id]['gcid'] = self._auth[user_id].gcid
                self._store[user_id]['expires_at'] = datetime.isoformat(self._auth[user_id].expires_at)
                write_store(self._store[user_id], user_id, self._primary_vehicle_id[user_id])
                log.debug("# after  write_store :" + str(self._auth[user_id].expires_at) +
                          "/" + self._auth[user_id].refresh_token)

        except Exception as err:
            # log.error("bmwbc.fetch_soc: requestData Error, vehicle_id: " + vehicle_id + f" {err=}, {type(err)=}")
            log.error("bmwbc.fetch_soc: requestData Error, vehicle_id: " + str(vehicle_id))
            # self._auth = None
            self._auth.pop(user_id, None)
            self._clconf.pop(user_id, None)
            self._account.pop(user_id, None)
            soc = 0
            range = 0.0
            soc_tsX = datetime.timestamp(datetime.now())
            # raise RequestFailed("SoC Request failed:\n" + str(err))
            raise Exception("SoC Request failed") from err
        return soc, range, soc_tsX


# main entry - _fetch needs to be run async
def fetch_soc(user_id: str, password: str, vin: str, captcha_token: str, vehicle_id: str) -> CarState:

    # prepare and call async method
    loop = new_event_loop()
    set_event_loop(loop)

    api = Api()

    # get soc, range, soc_timestamp from server
    soc, range, soc_tsX = loop.run_until_complete(api._fetch_soc(user_id, password, vin, captcha_token, vehicle_id))

    return CarState(soc=soc, range=range, soc_timestamp=soc_tsX)
