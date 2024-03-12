#!/usr/bin/env python3
import logging
from typing import Dict, List, Union

from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import MultiComponentUpdateContext
from modules.devices.enphase import counter, inverter, bat
from modules.devices.enphase.config import (EnphaseVersion,
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
        else:
            raise Exception(
                "illegal component type " + component_type + ". Allowed values: " +
                ','.join(self.COMPONENT_TYPE_TO_CLASS.keys())
            )

    def update(self) -> None:
        if self.device_config.configuration.version == EnphaseVersion.V2:
            # v2 requires token authentication
            if self.device_config.configuration.token is None:
                if self.device_config.configuration.user is None or self.device_config.configuration.password is None:
                    log.error("no valid token found and no credentials to authenticate!")
                    # ToDo: throw error and set fault state
                else:
                    log.info("no valid token found, trying to receive token with user/pass")
                    # ToDo: fetch token with user/pass
        log.debug("Start device reading " + str(self.components))
        if self.components:
            with MultiComponentUpdateContext(self.components):
                if self.device_config.configuration.version == EnphaseVersion.V1:
                    json_live_data = None  # ToDo: available in V1?
                    json_response = req.get_http_session().get(
                        'http://'+self.device_config.configuration.hostname+'/ivp/meters/readings', timeout=5).json()
                elif self.device_config.configuration.version == EnphaseVersion.V2:
                    json_live_data = req.get_http_session().get(
                        'https://'+self.device_config.configuration.hostname+'/ivp/livedata/status',
                        timeout=5, verify=False,
                        headers={"Authorization": f"Bearer {self.device_config.configuration.token}"}).json()
                    log.debug(f"livedata/status json response: {json_live_data}")
                    json_response = req.get_http_session().get(
                        'https://'+self.device_config.configuration.hostname+'/ivp/meters/readings',
                        timeout=5, verify=False,
                        headers={"Authorization": f"Bearer {self.device_config.configuration.token}"}).json()
                    log.debug(f"meters/readings json response: {json_response}")
                else:
                    log.error("unknown version: " + self.device_config.configuration.version)
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
