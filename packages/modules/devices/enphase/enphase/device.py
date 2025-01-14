#!/usr/bin/env python3
import jwt
import logging
import time
from typing import Iterable, Union

from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.enphase.enphase.bat import EnphaseBat
from modules.devices.enphase.enphase.config import (EnphaseVersion,
                                                    Enphase,
                                                    EnphaseCounterSetup,
                                                    EnphaseInverterSetup,
                                                    EnphaseBatSetup)
from modules.devices.enphase.enphase.counter import EnphaseCounter
from modules.devices.enphase.enphase.inverter import EnphaseInverter

log = logging.getLogger(__name__)


def create_device(device_config: Enphase):
    def create_bat_component(component_config: EnphaseBatSetup):
        nonlocal read_live_data
        read_live_data = True
        return EnphaseBat(device_config.id, component_config)

    def create_counter_component(component_config: EnphaseCounterSetup):
        return EnphaseCounter(device_config.id, component_config)

    def create_inverter_component(component_config: EnphaseInverterSetup):
        return EnphaseInverter(device_config.id, component_config)

    def check_token() -> bool:
        if (device_config.configuration.token is None or
                device_config.configuration.token == ""):
            log.info("no valid token found, trying to receive token")
            if receive_token() is False:
                return False
        try:
            token_exp = jwt.decode(
                device_config.configuration.token, options={"verify_signature": False})["exp"]
        except jwt.exceptions.InvalidTokenError as e:
            log.error("invalid token stored, trying to receive new token: " + str(e))
            if receive_token() is False:
                return False
            try:
                token_exp = jwt.decode(
                    device_config.configuration.token, options={"verify_signature": False})["exp"]
            except jwt.exceptions.InvalidTokenError as e:
                log.error("received token invalid: " + str(e))
                return False
        if token_exp < (time.time() + 3600*24):
            log.info("token will expire in less than one day, trying to receive new token")
            receive_token()
        return True

    def receive_token() -> bool:
        nonlocal token_tries
        if token_tries > 5:
            log.error("unsuccessfully tried 5 times to receive valid token, giving up. check log")
            return False
        if token_fails > 5:
            log.error("received 5 times a non-working token, giving up. check Envoy / gateway serial number")
            return False
        token_tries += 1
        if (device_config.configuration.user is None or
                device_config.configuration.password is None or
                device_config.configuration.serial is None):
            log.error("no credentials to authenticate to get token!")
            return False
        with req.get_http_session() as session:
            response = session.post(
                'https://enlighten.enphaseenergy.com/login/login.json?',
                data={'user[email]': device_config.configuration.user,
                      'user[password]': device_config.configuration.password},
                timeout=5)
            if response.ok is False:
                log.error(f"could not authenticate at enphase, check credentials. "
                          f"HTTP status code returned: {response.status_code}")
                return False
            response_json = response.json()
            response = session.post(
                'https://entrez.enphaseenergy.com/tokens',
                json={'session_id': response_json['session_id'],
                      'serial_num': device_config.configuration.serial,
                      'username': device_config.configuration.user},
                timeout=5)
            if response.ok is False:
                log.error(f"could not receive token from enphase, check Envoy serial number. "
                          f"HTTP status code returned: {response.status_code}")
                return False
            token_tries = 0
            token = response.text.strip()
            log.info(f"received new token: {token}")
            device_config.configuration.token = token
            try:
                log.debug("saving new access token")
                Pub().pub("openWB/set/system/device/" + str(device_config.id) + "/config",
                          asdict(device_config))
            except Exception as e:
                log.exception('Token mqtt write exception ' + str(e))
                return False
            return True

    def update_components(components: Iterable[Union[EnphaseBat, EnphaseCounter, EnphaseInverter]]):
        nonlocal token_fails
        if device_config.configuration.version == EnphaseVersion.V2.value:
            # v2 requires token authentication
            if check_token() is False:
                log.error("no valid token to connect to envoy")
                return
        log.debug("Start device reading " + str(components))
        with req.get_http_session() as session:
            json_live_data = None
            if device_config.configuration.version == EnphaseVersion.V1.value:
                json_response = session.get(
                    'http://'+device_config.configuration.hostname+'/ivp/meters/readings',
                    timeout=5).json()
                # json_live_data does not exist on older firmware
            elif device_config.configuration.version == EnphaseVersion.V2.value:
                response = session.get(
                    'https://'+device_config.configuration.hostname+'/ivp/meters/readings',
                    timeout=5, verify=False,
                    headers={"Authorization": f"Bearer {device_config.configuration.token}"})
                if response.ok is False:
                    log.info("token invalid, will be renewed if credentials are set")
                    device_config.configuration.token = None
                    token_fails += 1
                    return
                token_fails = 0
                json_response = response.json()
                log.debug(f"meters/readings json response: {json_response}")
                if read_live_data:
                    json_live_data = session.get(
                        'https://'+device_config.configuration.hostname+'/ivp/livedata/status',
                        timeout=5, verify=False,
                        headers={"Authorization": f"Bearer {device_config.configuration.token}"}).json()
                    log.debug(f"livedata/status json response: {json_live_data}")
            else:
                log.error(f"unknown version: {device_config.configuration.version}")
                return
            for component in components:
                component.update(json_response, json_live_data)

    read_live_data = False
    token_tries = 0
    token_fails = 0
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Enphase)
