#!/usr/bin/env python3

# collection of common utilities
# used by vehicle soc/range modules

from typing import Union, Optional
import logging
from asyncio import wait_for, get_event_loop, new_event_loop, set_event_loop, TimeoutError
from functools import partial
from datetime import datetime
from time import time
from jwt import decode
from helpermodules.pub import Pub
from json import dump, dumps, load, loads
import paho.mqtt.subscribe as subscribe
from modules.common.configurable_vehicle import ConfigurableVehicle
from control import data
from modules.common.component_state import CarState
from modules.common.store._car import CarValueStoreBroker
from modules.common import store


DEF_LOGFILTER = '__'

# define how to get core data, via 'core' (object tree access) or 'mqtt' (subscribe.simple)
MODE_MQTT = 'mqtt'
MODE_CORE = 'core'
GET_MODE = MODE_CORE

# timeout for mqtt subscribe.sumple
MQTT_TIMEOUT = 1

log = logging.getLogger(__name__)


# logUtils - filtered logging
# if logFilter is defined log filtered messages only otherwise log normally on INFO level
class logUtils:

    def __init__(self, filter: Optional[str] = None):
        if filter:
            self.logFilter = filter
        else:
            self.logFilter = DEF_LOGFILTER

    def set_logFilter(self, filter: str = ''):
        self.logFilter = filter

    # get logFilter via core data access
    def get_logFilter(self, vehicle: int) -> str:
        if GET_MODE == MODE_CORE:
            su = socUtils(self)
            try:
                self.logFilter = su.get_vehicle_config_logFilter(vehicle)
            except Exception as e:
                log.exception("get_logFilter error: %s", e)
                self.logFilter = DEF_LOGFILTER
            self.infoLog('Q', 'get_logFilter: logFilter=' + self.logFilter)
        elif GET_MODE == MODE_MQTT:
            mq = mqttUtils(self)
            try:
                msg = mq.mqtt_get_topic("openWB/vehicle/" + vehicle + "/soc_module/config", "localhost")
                config = loads(str(msg.payload, 'utf-8'))
                if 'logFilter' in config['configuration']:
                    self.logFilter = config['configuration']['logFilter']
                    if self.logFilter is None:
                        self.logFilter = DEF_LOGFILTER
                else:
                    self.logFilter = DEF_LOGFILTER
            except Exception as e:
                log.exception("get_logFilter mqtt error: %s", e)
                self.logFilter = DEF_LOGFILTER
            self.infoLog('Q', 'get_logFilter: logFilter=' + self.logFilter)
        else:
            log.ERROR("get_logFilter: unknown GET_MODE=" + str(GET_MODE))
            raise
        return self.logFilter

    def infoLog(self, filter: str, txt: str):
        if self.logFilter != DEF_LOGFILTER:
            if filter in self.logFilter or 'A' in self.logFilter:
                log.info('(' + filter + '): ' + txt)
        else:
            log.info(txt + ', filter=' + filter + ', logFilter=' + self.logFilter)


# mqtt section
class mqttUtils:

    def __init__(self, lu: Optional[logUtils] = None):
        if lu:
            self.lu = lu
        else:
            self.lu = logUtils()

    # write rsp. publish vehicle configuration
    def write_config(self, topic: str, config: dict):
        try:
            self.lu.infoLog('i', "write_config:\n" + dumps(config, ensure_ascii=False, indent=4))
            Pub().pub(topic, config)
        except Exception as e:
            log.exception('Token mqtt write exception ' + str(e))

    # get mqtt content by topic - async to avoid subscribe.simple from blocking
    # this would be blocking if not called async
    def _mqtt_get_topic(self, topic: str, host: str):
        try:
            msg = subscribe.simple(topic, hostname=host)
        except Exception as e:
            log.exception("_mqtt_get_topic error: %s", e)
            raise
        return msg

    # async function with timeout in case above function is blocking
    async def _mqtt_get_topic_async(self, topic: str, host: str):
        try:
            msg = await wait_for(
                self.loop.run_in_executor(None, partial(self._mqtt_get_topic, topic, host)), timeout=MQTT_TIMEOUT)
        except TimeoutError:
            pass
            msg = None
        return msg

    # get message from mqtt server in async mode
    def mqtt_get_topic(self, topic: str, host: str):
        try:
            try:
                self.loop = get_event_loop()
            except Exception as e:
                if str(e).startswith('There is no current event loop in thread'):
                    self.loop = new_event_loop()
                    set_event_loop(self.loop)
                else:
                    raise
            msg = self.loop.run_until_complete(self._mqtt_get_topic_async(topic, host))
            log.debug("mqtt_get_topic: msg.payload=" + str(msg.payload, 'utf-8'))
        except Exception as e:
            log.exception("mqtt_get_topic error: %s", e)
            msg = None
        return msg


# file utilities, loading and writing json files
class fileUtils:

    def __init__(self, lu: Optional[logUtils] = None):
        if lu:
            self.lu = lu
        else:
            self.lu = logUtils()

    # load store from file, call initialize function file doesn't exist
    def load_json_file(self, storeFile: str, initFunc) -> dict:
        try:
            with open(storeFile, 'r', encoding='utf-8') as tf:
                store = load(tf)
        except FileNotFoundError:
            self.lu.infoLog("i", "load_store: store file not found, return init store")
            store = initFunc()
        except Exception as e:
            self.lu.infoLog('i', "init: loading stored data failed, file: " +
                            storeFile + ", error=" + str(e))
            store = initFunc()
        return store

    # write dict to json file
    def write_json_file(self, storeFile: str, store: dict):
        try:
            with open(storeFile, 'w', encoding='utf-8') as tf:
                dump(store, tf, indent=4)
        except Exception as e:
            self.lu.infoLog('i', "write_json_file: Exception " + str(e))
        return


# functions supporting vehicle modules
class socUtils(fileUtils):

    def __init__(self, lu: Optional[logUtils] = None):
        super().__init__()
        if lu:
            self.lu = lu
        else:
            self.lu = logUtils()
        self.mq = mqttUtils(self.lu)

    # publish CarState via core store
    def set_CarState(self, vehicle: int, soc: int, range: float, ts: int):
        try:
            st: CarValueStoreBroker = store.get_car_value_store(vehicle)
            carState: CarState = CarState(int(soc), float(range), round(time(), 2))
            st.set(carState)
            st.update()
        except Exception as e:
            log.exception("set_CarState Error: %s", e)
        return

    # get CarState for vehicle from core data
    def get_CarState(self, vehicle: int) -> CarState:
        for ev in data.data.ev_data.values():
            if ev.num == vehicle:
                evGet: ConfigurableVehicle.EvData.Get = ev.data.get
                carState: CarState = CarState(evGet.soc, evGet.range, evGet.soc_timestamp)
                break
        else:
            carState: CarState = CarState(None, None, None)
        return carState

    # get config of vehicle by number
    def get_vehicle_config(self, vehicle: int) -> dict:
        try:
            ev_data = data.data.ev_data.copy()
            for ev in ev_data.values():
                if int(ev.num) == int(vehicle):
                    cv: ConfigurableVehicle = ev.soc_module
                    se = cv.vehicle_config.toJSON()
                    # sc = se.configuration.toJSON()
                    break
            else:
                se = "{}"
                # sc = "{}"
                log.info('get_vehicle_config: ev=' + str(vehicle) + ' not found')
        except Exception as e:
            se = "{}"
            # sc = "{}"
            log.info('get_vehicle_config: Error: ' + str(e))
        sed = loads(se)
        # scd = loads(sc)
        return sed
        # return scd

    # get logFilter from config of vehicle by number
    def get_vehicle_config_logFilter(self, vehicle: int) -> str:
        try:
            sed = self.get_vehicle_config(vehicle)
            scd = sed['configuration']
            # scd = self.get_vehicle_config(vehicle)
            try:
                lf = scd['logFilter']
                # log.info('get_vehicle_config_logFilter: ev=' + str(vehicle) + ", logFilter=" + lf)
            except Exception as e:
                log.info('get_vehicle_config_logFilter: Error: ' + str(e))
                lf = DEF_LOGFILTER
        except Exception as e:
            log.info('get_vehicle_config_logFilter: Error: ' + str(e))
            lf = DEF_LOGFILTER
        return lf

    # get mapping of vehicle vin and number of type Type from core ev_data
    def get_vin_ev_map(self, Type: str) -> dict:
        vh_list = {}
        # get vin->ev.num mapping from ev_data object
        ev_data = data.data.ev_data.copy()
        for ev in ev_data.values():
            if isinstance(ev.soc_module, ConfigurableVehicle):
                cv: ConfigurableVehicle = ev.soc_module
                se = cv.vehicle_config
                if se.type == Type:
                    sc = se.configuration
                    self.lu.infoLog('i', 'ev_data: ev=' + str(ev.num) + ', sc.vin=' + str(sc.vin))
                    vh_list[sc.vin] = ev.num
        return vh_list

    # get expiration from jwt token
    def get_token_expiration(self, token: str, fmt: str) -> Union[int, str]:
        try:
            self.token_dec = decode(token, 'utf-8', options={"verify_signature": False})
            self.exp = self.token_dec['exp']
            self.exp_dt = datetime.fromtimestamp(self.exp).strftime(fmt)
        except Exception as e:
            log.exception('get_token_expiration error ' + str(e))
            self.exp = None
            self.exp_dt = None
        return self.exp, self.exp_dt

    # check dict for a list of keys
    def keys_exist(self, element, *keys):
        # Check if *keys (nested) exists in `element` (dict).
        if not isinstance(element, dict):
            raise AttributeError('keys_exists() expects dict as first argument.')
        if len(keys) == 0:
            raise AttributeError('keys_exists() expects at least two arguments, one given.')

        _element = element
        for key in keys:
            try:
                _element = _element[key]
            except KeyError:
                return False
        return True

    # update vehicle configuration with updates
    def update_vehicle_config(self, vehicle: int, conf_update: dict):
        if GET_MODE == MODE_CORE:
            confDict = self.get_vehicle_config(vehicle)
        elif GET_MODE == MODE_MQTT:
            cfg_getTopic = "openWB/vehicle/" + str(vehicle) + "/soc_module/config"
            # get config dict from broker
            msg = self.mq.mqtt_get_topic(cfg_getTopic, "localhost")
            confDict = loads(str(msg.payload, 'utf-8'))
        else:
            log.ERROR("update_vehicle_config: unknown GET_MODE=" + str(GET_MODE))
            raise

        self.lu.infoLog('T', "update_vehicle_config: confDict_org=" + dumps(confDict, indent=4))
        # update values in conf_update
        for k, v in conf_update.items():
            confDict['configuration'][k] = v
        self.lu.infoLog('T', "update_vehicle_config: confDict_new=" + dumps(confDict, indent=4))

        cfg_setTopic = "openWB/set/vehicle/" + str(vehicle) + "/soc_module/config"
        self.mq.write_config(
            cfg_setTopic,
            confDict)
        return
