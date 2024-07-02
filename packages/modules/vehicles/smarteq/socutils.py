#!/usr/bin/env python3

from typing import Union
import logging
from datetime import datetime
from time import time
from jwt import decode
from helpermodules.pub import Pub
# from json import dumps
from control import data
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.common.component_state import CarState
from modules.common.store._car import CarValueStoreBroker
from modules.common import store


log = logging.getLogger(__name__)


class socUtils:

    def __init__(self):
        pass

    def read_token_file(self, path: str) -> str:
        try:
            with open(path, "r") as tf:           # try to open Token file
                token = tf.read()              # read token
        except Exception:
            token = None                # if no old token found set Token_old to dummy value
        return token

    def write_token_file(self, path: str, token: str, config={}):
        try:
            # log.debug("store Token in file " + path)
            with open(path, "w") as tf:
                tf.write(token)         # write Token file
        except Exception as e:
            log.exception('Token file write exception ' + str(e))

    def write_token_mqtt(self, topic: str, token: str, opMode: str, config={}):
        try:
            config['configuration']['refreshToken'] = token
            config['configuration']['opMode'] = opMode
            # log.debug("write_token_mqtt:\n" + dumps(config, ensure_ascii=False, indent=4))
            Pub().pub(topic, config)
        except Exception as e:
            log.exception('Token mqtt write exception ' + str(e))

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
                    log.debug('ev_data: ev=' + str(ev.num) + ', sc.vin=' + str(sc.vin))
                    vh_list[sc.vin] = ev.num
        return vh_list

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
