#!/usr/bin/env python3

from typing import Union
import logging
import datetime
import time
import jwt
from helpermodules.pub import Pub
import threading
import json
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
from control import data
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.smarteq.config import SmartEQ, SmartEQConfiguration


initialToken = '1.2.3'
threadname = 'Soc_smarteq_mqtt'

log = logging.getLogger(__name__)
vehicleList = {}
vehicleConfig = {}
logFilter = 'q'


def _infoLog(filter: str, txt: str):
    global logFilter
    if filter in logFilter or 'A' in logFilter:
        log.info('(' + filter + '): ' + txt)


def mqtt_on_connect(client, userdata, flags, rc):
    global threadname
    threading.current_thread().name = threadname
    try:
        if rc != 0:
            log.error('mqtt_on_connect: failure: ' + str(rc))
        client.subscribe("openWB/vehicle/+/soc_module/config")
    except Exception as e:
        log.exception("mqtt_on_connect error: %s", e)


def mqtt_on_message(client, userdata, msg):
    global threadname
    global vehicleList
    global vehicleConfig
    try:
        threading.current_thread().name = threadname
        ev = msg.topic.split('/')[2]
        m = json.loads(str(msg.payload, 'utf-8'))
        if 'type' in m and m['type'] == 'smarteq':
            vin = m['configuration']['vin']
            _infoLog('Q', "mqtt_on_message smarteq: ev=" + ev + ', config =\n' + json.dumps(m, indent=4))
            vehicleConfig[ev] = m
            vehicleList[vin] = ev
    except Exception as e:
        log.exception("mqtt_on_message error: %s", e)


class socUtils:

    def __init__(self):
        global threadname
        global logFilter
        logFilter = 'q'
        threadname = 'soc_smarteq_mqtt'

    def get_vin_ev_map(self) -> dict:
        vh_list = {}
        # try to get vin->ev.num mapping from ev_data object
        for ev in data.data.ev_data.values():
            # log.info('ev_data: ev=' + str(ev.num) + ', soc_module=' + str(ev.soc_module))
            if isinstance(ev.soc_module, ConfigurableVehicle):
                cv: ConfigurableVehicle = ev.soc_module
                # log.info('ev_data: ev=' + str(ev.num) + ', cv.vehicle=' + str(cv.vehicle))
                if isinstance(cv.vehicle_config, SmartEQ):
                    se: SmartEQ = cv.vehicle_config
                    # log.info('ev_data: ev=' + str(ev.num) + ', se.name/type=' + str(se.name) + '/' + str(se.type))
                    if isinstance(se.configuration, SmartEQConfiguration):
                        sc: SmartEQConfiguration = se.configuration
                        _infoLog('i', 'ev_data: ev=' + str(ev.num) + ', sc.vin=' + str(sc.vin))
                        vh_list[sc.vin] = ev.num
        return vh_list

    def read_token_file(self, path: str) -> str:
        try:
            self.tf = open(path, "r")           # try to open Token file
            token = self.tf.read()              # read token
            self.tf.close()
        except Exception:
            token = None                # if no old token found set Token_old to dummy value
        return token

    def write_token_file(self, path: str, token: str, config={}):
        try:
            _infoLog('s', "store Token in file " + path)
            self.tf = open(path, "w")
            self.tf.write(token)         # write Token file
            self.tf.close()
        except Exception as e:
            log.exception('Token file write exception ' + str(e))

    def write_token_mqtt(self, topic: str, token: str, opMode: str, config={}):
        try:
            config['configuration']['refreshToken'] = token
            config['configuration']['opMode'] = opMode
            _infoLog('i', "write_token_mqtt:\n" + json.dumps(config, ensure_ascii=False, indent=4))
            Pub().pub(topic, config)
        except Exception as e:
            log.exception('Token mqtt write exception ' + str(e))

    def get_token_expiration(self, token: str, fmt: str) -> Union[int, str]:
        try:
            self.token_dec = jwt.decode(token, 'utf-8', options={"verify_signature": False})
            self.exp = self.token_dec['exp']
            self.exp_dt = datetime.datetime.fromtimestamp(self.exp).strftime(fmt)
        except Exception as e:
            log.exception('get_token_expiration error ' + str(e))
            self.exp = None
            self.exp_dt = None

        return self.exp, self.exp_dt

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

    def set_logFilter(self, filter: str = ''):
        global logFilter
        logFilter = filter

    def set_threadname(self, name: str):
        global threadname
        threadname = name

    def _get_vehicleList(self) -> Union[dict, dict]:
        global vehicleList
        global vehicleConfig
        try:
            vehicleList = {}
            vehicleConfig = {}

            client = mqtt.Client()
            client.on_connect = mqtt_on_connect
            client.on_message = mqtt_on_message

            client.connect("localhost", 1883, 60)

            client.loop_start()
            time.sleep(2)
            client.disconnect()
            client.loop_stop()
        except Exception as e:
            log.exception("_get_vehicleList mqtt error: %s", e)

        _infoLog('Q', '_get_vehicleList: vehicleList=\n' + json.dumps(vehicleList, indent=4))
        _infoLog('Q', '_get_vehicleList: vehicleConfig=\n' + json.dumps(vehicleConfig, indent=4))

        return vehicleList, vehicleConfig

    def _get_logFilter(self) -> str:
        global logFilter
        try:
            logFilter = ''
            msg = subscribe.simple("openWB/vehicle/3/soc_module/config", hostname="localhost")
            config = json.loads(str(msg.payload, 'utf-8'))
            if 'logFilter' in config['configuration']:
                logFilter = config['configuration']['logFilter']
                if logFilter is None:
                    logFilter = ''
        except Exception as e:
            log.exception("_get_logFilter mqtt error: %s", e)
        _infoLog('Q', '_get_logFilter: logFilter=' + logFilter)
        return logFilter

    # publish a single message to 1883 broker
    def pub(self, topic: str, payload: str):
        try:
            _infoLog('q', "pub: topic=" + topic + ', payload=' + payload)
            client = mqtt.Client()
            client.connect("localhost", 1883, 60)
            ret, mid = client.publish(topic, payload)
            if ret != 0:
                _infoLog('q', "pub: topic=" + topic +
                         ', payload=' + payload +
                         ', ret=' + str(ret) +
                         ', mid=' + str(mid))
            client.disconnect()
        except Exception as e:
            log.exception("pub mqtt error: %s", e)

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
            _ts = time.time()
            # self.pub(topic, str(_ts))
            msgs.append({'topic': topic, 'payload': str(_ts)})
            _infoLog('Q', "set_CarState publish.multiple: msgs=\n" + json.dumps(msgs))
            _infoLog('q', "set_CarState: " + str(soc) + '%/' + str(range) + 'KM@' + str(_ts))
            publish.multiple(msgs, hostname='localhost', port=1883)
        except Exception as e:
            log.exception("set_CarState error: %s", e)
