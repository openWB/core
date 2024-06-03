#!/usr/bin/env python3

# collection of common utilities
# used by vehicle soc/range modules

from typing import Union, Optional
import logging
from datetime import datetime
from time import time
from jwt import decode
from helpermodules.pub import Pub
from json import dump, dumps, load, loads
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from modules.common.configurable_vehicle import ConfigurableVehicle
from control import data
from modules.common.component_state import CarState


DEF_LOGFILTER = '__'

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

    # get logFilter via mqtt
    def get_logFilter(self, vnum: str) -> str:
        mq = mqttUtils(self)
        try:
            msg = mq.mqtt_get_topic("openWB/vehicle/" + vnum + "/soc_module/config", "localhost")
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

    # publish a single message to 1883 broker
    def pub(self, topic: str, payload: str):
        try:
            self.lu.infoLog('q', "pub: topic=" + topic + ', payload=' + payload)
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            ret, mid = client.publish(topic, payload)
            if ret != 0:
                self.lu.infoLog('q', "pub: topic=" + topic +
                                ', payload=' + payload +
                                ', ret=' + str(ret) +
                                ', mid=' + str(mid))
            client.disconnect()
        except Exception as e:
            log.exception("pub mqtt error: %s", e)

    # get mqtt content by topic
    def mqtt_get_topic(self, topic: str, host: str):
        try:
            msg = subscribe.simple(topic, hostname=host)
        except Exception as e:
            log.exception("mqtt_get_topic error: %s", e)
            raise
        return msg

    # publish CarState via MQTT to 1883 broker
    def set_CarState(self, ev: int, soc: int, range: float, ts: int):
        try:
            msgs = []
            topic = 'openWB/set/vehicle/' + str(ev) + '/get/soc'
            # self.pub(topic, str(soc))
            msgs.append({'topic': topic, 'payload': str(soc)})
            topic = 'openWB/set/vehicle/' + str(ev) + '/get/range'
            # self.pub(topic, str(range))
            msgs.append({'topic': topic, 'payload': str(range)})
            topic = 'openWB/set/vehicle/' + str(ev) + '/get/soc_timestamp'
            _ts = time()
            # self.pub(topic, str(_ts))
            msgs.append({'topic': topic, 'payload': str(_ts)})
            self.lu.infoLog('Q', "set_CarState publish.multiple: msgs=\n" + dumps(msgs))
            self.lu.infoLog('q', "set_CarState: " + str(soc) + '%/' + str(range) + 'KM@' + str(_ts))
            publish.multiple(msgs, hostname='localhost', port=1883)
        except Exception as e:
            log.exception("set_CarState error: %s", e)
        return


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

    # get CarState for vehicle
    def get_CarState(self, vehicle: int) -> CarState:
        for ev in data.data.ev_data.values():
            if ev.num == vehicle:
                evGet: ConfigurableVehicle.EvData.Get = ev.data.get
                carState: CarState = CarState(evGet.soc, evGet.range, evGet.soc_timestamp)
                break
        else:
            carState: CarState = CarState(None, None, None)
        return carState

    # get mapping of vehicle vin and number of type Type from core ev_data
    def get_vin_ev_map(self, Type: str) -> dict:
        vh_list = {}
        # get vin->ev.num mapping from ev_data object
        for ev in data.data.ev_data.values():
            if isinstance(ev.soc_module, ConfigurableVehicle):
                cv: ConfigurableVehicle = ev.soc_module
                if cv.vehicle_config.type == Type:
                    se = cv.vehicle_config
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

    # update vehicle configuration with updatee
    def update_vehicle_config(self, vehicle: int, conf_update: dict):
        cfg_setTopic = "openWB/set/vehicle/" + str(vehicle) + "/soc_module/config"
        cfg_getTopic = "openWB/vehicle/" + str(vehicle) + "/soc_module/config"
        # get config dict from broker
        msg = self.mq.mqtt_get_topic(cfg_getTopic, "localhost")
        confDict = loads(str(msg.payload, 'utf-8'))

        self.lu.infoLog('T', "update_vehicle_config: confDict_org=" + dumps(confDict, indent=4))
        # update values in conf_update
        for k, v in conf_update.items():
            confDict['configuration'][k] = v
        self.lu.infoLog('T', "update_vehicle_config: confDict_new=" + dumps(confDict, indent=4))

        self.mq.write_config(
            cfg_setTopic,
            confDict)
