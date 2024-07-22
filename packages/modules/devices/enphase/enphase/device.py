#!/usr/bin/env python3
import jwt
import logging
import re
import time
from typing import Dict, List, Union
from dataclass_utils import asdict, dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import MultiComponentUpdateContext
from modules.devices.enphase.enphase import counter, inverter, bat
from modules.devices.enphase.enphase.config import (EnphaseVersion,
                                                    Enphase,
                                                    EnphaseConfiguration,
                                                    EnphaseCounterConfiguration,
                                                    EnphaseCounterSetup,
                                                    EnphaseInverterConfiguration,
                                                    EnphaseInverterSetup,
                                                    EnphaseBatConfiguration,
                                                    EnphaseBatSetup)

log = logging.getLogger(__name__)

enphase_component_classes = Union[counter.EnphaseCounter, inverter.EnphaseInverter, bat.EnphaseBat]


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "counter": counter.EnphaseCounter,
        "inverter": inverter.EnphaseInverter,
        "bat": bat.EnphaseBat,
    }

    def __init__(self, device_config: Union[Dict, Enphase]) -> None:
        self.components = {}  # type: Dict[str, enphase_component_classes]
        self.read_live_data = False
        self.token_tries = 0
        self.token_fails = 0
        try:
            self.device_config = dataclass_from_dict(Enphase, device_config)
        except Exception:
            log.exception("Fehler im Modul "+self.device_config.name)

    def add_component(
        self,
        component_config: Union[Dict, EnphaseCounterSetup, EnphaseInverterSetup, EnphaseBatSetup]
    ) -> None:
        if isinstance(component_config, Dict):
            component_type = component_config["type"]
        else:
            component_type = component_config.type
        component_config = dataclass_from_dict(COMPONENT_TYPE_TO_MODULE[
            component_type].component_descriptor.configuration_factory, component_config)
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config.id)] = self.COMPONENT_TYPE_TO_CLASS[component_type](
                self.device_config.id, component_config)
            if "bat" in component_type:
                self.read_live_data = True
        else:
            raise Exception(
                "illegal component type " + component_type + ". Allowed values: " +
                ','.join(self.COMPONENT_TYPE_TO_CLASS.keys())
            )

    def auto_set_version(self) -> None:
        response = req.get_http_session().get(
            'http://'+self.device_config.configuration.hostname+'/',
            timeout=5, allow_redirects=False)
        if response.status_code == 200:
            self.device_config.configuration.version = EnphaseVersion.V1.value
        elif response.status_code == 301:
            if response.headers.get('Location', '').startswith('https'):
                self.device_config.configuration.version = EnphaseVersion.V2.value
            else:
                self.device_config.configuration.version = EnphaseVersion.V1.value
        else:
            log.error("Could not identify Envoy firmware version")
            return
        try:
            log.debug("saving envoy version")
            Pub().pub("openWB/set/system/device/" + str(self.device_config.id) + "/config", asdict(self.device_config))
        except Exception as e:
            log.exception('Token mqtt write exception ' + str(e))

    def auto_set_serial(self) -> None:
        if self.device_config.configuration.version == EnphaseVersion.V1.value:
            response = req.get_http_session().get(
                'http://'+self.device_config.configuration.hostname+'/',
                timeout=5)
        elif self.device_config.configuration.version == EnphaseVersion.V2.value:
            response = req.get_http_session().get(
                'https://'+self.device_config.configuration.hostname+'/',
                timeout=5, verify=False)
        else:
            log.error(f"unknown version: {self.device_config.configuration.version}")
            return
        pattern = re.compile('<title.*>.* ([0-9]+)</title>')
        match = re.search(pattern, response.text)
        if match is None:
            log.error("could not find Envoy serial")
            return
        self.device_config.configuration.serial = match.group(1)
        try:
            log.debug("saving envoy serial")
            Pub().pub("openWB/set/system/device/" + str(self.device_config.id) + "/config", asdict(self.device_config))
        except Exception as e:
            log.exception('Token mqtt write exception ' + str(e))

    def find_counter_eid(self, measurement_type: str) -> str:
        if self.device_config.configuration.version == EnphaseVersion.V1.value:
            json_response = req.get_http_session().get(
                'http://'+self.device_config.configuration.hostname+'/ivp/meters', timeout=5).json()
        elif self.device_config.configuration.version == EnphaseVersion.V2.value:
            # v2 requires token authentication
            if self.check_token() is False:
                log.error("no valid token to connect to envoy")
                return
            response = req.get_http_session().get(
                'https://'+self.device_config.configuration.hostname+'/ivp/meters',
                timeout=5, verify=False,
                headers={"Authorization": f"Bearer {self.device_config.configuration.token}"})
            if response.ok is False:
                log.info("token invalid, will be renewed if credentials are set")
                self.device_config.configuration.token = None
                self.token_fails += 1
                return
            self.token_fails = 0
            json_response = response.json()
        for cnt in json_response:
            if cnt.get('measurementType') == measurement_type:
                return str(cnt.get('eid'))

    def check_token(self) -> bool:
        if (self.device_config.configuration.token is None or
                self.device_config.configuration.token == ""):
            log.info("no valid token found, trying to receive token")
            if self.receive_token() is False:
                return False
        try:
            token_exp = jwt.decode(
                self.device_config.configuration.token, options={"verify_signature": False})["exp"]
        except jwt.exceptions.InvalidTokenError as e:
            log.error("invalid token stored, trying to receive new token: " + str(e))
            if self.receive_token() is False:
                return False
            try:
                token_exp = jwt.decode(
                    self.device_config.configuration.token, options={"verify_signature": False})["exp"]
            except jwt.exceptions.InvalidTokenError as e:
                log.error("received token invalid: " + str(e))
                return False
        if token_exp < (time.time() + 3600*24):
            log.info("token will expire in less than one day, trying to receive new token")
            self.receive_token()
        return True

    def receive_token(self) -> bool:
        if self.token_tries > 5:
            log.error("unsuccessfully tried 5 times to receive valid token, giving up. check log")
            return False
        if self.token_fails > 5:
            log.error("received 5 times a non-working token, giving up. check Envoy / gateway serial number")
            return False
        self.token_tries += 1
        if (self.device_config.configuration.user is None or
                self.device_config.configuration.password is None or
                self.device_config.configuration.serial is None):
            log.error("no credentials to authenticate to get token!")
            return False
        with req.get_http_session() as session:
            response = session.post(
                'https://enlighten.enphaseenergy.com/login/login.json?',
                data={'user[email]': self.device_config.configuration.user,
                      'user[password]': self.device_config.configuration.password},
                timeout=5)
            if response.ok is False:
                log.error(f"could not authenticate at enphase, check credentials. "
                          f"HTTP status code returned: {response.status_code}")
                return False
            response_json = response.json()
            response = session.post(
                'https://entrez.enphaseenergy.com/tokens',
                json={'session_id': response_json['session_id'],
                      'serial_num': self.device_config.configuration.serial,
                      'username': self.device_config.configuration.user},
                timeout=5)
            if response.ok is False:
                log.error(f"could not receive token from enphase, check Envoy serial number. "
                          f"HTTP status code returned: {response.status_code}")
                return False
            self.token_tries = 0
            token = response.text.strip()
            log.info(f"received new token: {token}")
            self.device_config.configuration.token = token
            try:
                log.debug("saving new access token")
                Pub().pub("openWB/set/system/device/" + str(self.device_config.id) + "/config",
                          asdict(self.device_config))
            except Exception as e:
                log.exception('Token mqtt write exception ' + str(e))
                return False
            return True

    def update(self) -> None:
        if self.components:
            with MultiComponentUpdateContext(self.components):
                if self.device_config.configuration.version == EnphaseVersion.V2.value:
                    # v2 requires token authentication
                    if self.check_token() is False:
                        log.error("no valid token to connect to envoy")
                        return
                log.debug("Start device reading " + str(self.components))
                with req.get_http_session() as session:
                    json_live_data = None
                    if self.device_config.configuration.version == EnphaseVersion.V1.value:
                        json_response = session.get(
                            'http://'+self.device_config.configuration.hostname+'/ivp/meters/readings',
                            timeout=5).json()
                        # json_live_data does not exist on older firmware
                    elif self.device_config.configuration.version == EnphaseVersion.V2.value:
                        response = session.get(
                            'https://'+self.device_config.configuration.hostname+'/ivp/meters/readings',
                            timeout=5, verify=False,
                            headers={"Authorization": f"Bearer {self.device_config.configuration.token}"})
                        if response.ok is False:
                            log.info("token invalid, will be renewed if credentials are set")
                            self.device_config.configuration.token = None
                            self.token_fails += 1
                            return
                        self.token_fails = 0
                        json_response = response.json()
                        log.debug(f"meters/readings json response: {json_response}")
                        if self.read_live_data:
                            json_live_data = session.get(
                                'https://'+self.device_config.configuration.hostname+'/ivp/livedata/status',
                                timeout=5, verify=False,
                                headers={"Authorization": f"Bearer {self.device_config.configuration.token}"}).json()
                            log.debug(f"livedata/status json response: {json_live_data}")
                    else:
                        log.error(f"unknown version: {self.device_config.configuration.version}")
                        return
                    for component in self.components:
                        self.components[component].update(json_response, json_live_data)
        else:
            log.warning(
                self.device_config.name +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )


COMPONENT_TYPE_TO_MODULE = {
    "counter": counter,
    "inverter": inverter,
    "bat": bat
}


def read_legacy(hostname: str, component_config: Union[EnphaseCounterSetup, EnphaseInverterSetup]) -> None:
    dev = Device(Enphase(configuration=EnphaseConfiguration(hostname=hostname)))
    dev.add_component(component_config)
    dev.update()


def read_legacy_counter(ip_address: str, eid: str):
    config = EnphaseCounterConfiguration(eid=eid)
    read_legacy(
        ip_address,
        counter.component_descriptor.configuration_factory(id=None, configuration=config))


def read_legacy_inverter(ip_address: str, eid: str, num: int):
    config = EnphaseInverterConfiguration(eid=eid)
    read_legacy(ip_address, inverter.component_descriptor.configuration_factory(id=num, configuration=config))


def read_legacy_bat(ip_address: str, eid: str, num: int):
    config = EnphaseBatConfiguration()
    read_legacy(ip_address, bat.component_descriptor.configuration_factory(id=num, configuration=config))


def main(argv: List[str]):
    run_using_positional_cli_args(
        {"counter": read_legacy_counter, "inverter": read_legacy_inverter}, argv
    )


device_descriptor = DeviceDescriptor(configuration_factory=Enphase)
