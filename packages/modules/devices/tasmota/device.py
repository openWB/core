#!/usr/bin/env python3
import logging
from typing import Dict, Optional, List, Union

from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.devices.tasmota import counter
from modules.devices.tasmota.config import Tasmota, TasmotaCounterSetup
from modules.common import req
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext

log = logging.getLogger(__name__)


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "counter": counter.TasmotaCounter,
    }

    def __init__(self, device_config: Union[Dict, Tasmota]) -> None:
        self.components = {}  # type: Dict[str, counter.TasmotaCounter]
        try:
            self.device_config = dataclass_from_dict(Tasmota, device_config)
            self.url = self.device_config.configuration.url
        except Exception:
            log.exception("Fehler im Modul "+self.device_config.name)

    def add_component(self, component_config: Union[Dict, TasmotaCounterSetup]) -> None:
        if isinstance(component_config, Dict):
            # log.info("tasmota: device.add_component.isinstance-true")
            component_type = component_config["type"]
        else:
            # log.info("tasmota: device.add_component.isinstance-false")
            component_type = component_config.type
        component_config = dataclass_from_dict(COMPONENT_TYPE_TO_MODULE[
            component_type].component_descriptor.configuration_factory, component_config)
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config.id)] = self.COMPONENT_TYPE_TO_CLASS[component_type](
                self.device_config.id, component_config, self.url)
        else:
            raise Exception(
                "illegal component type " + component_type + ". Allowed values: " +
                ','.join(self.COMPONENT_TYPE_TO_CLASS.keys())
            )

    def update(self) -> None:
        response = req.get_http_session().get(self.url, timeout=5).json()
        if self.components:
            for component in self.components:
                with SingleComponentUpdateContext(self.components[component].component_info):
                    self.components[component].update(response)
        else:
            log.warning(
                self.device_config.name +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )


COMPONENT_TYPE_TO_MODULE = {
    "counter": counter
    }


def read_legacy(component_type: str, url: str, num: Optional[int] = None) -> None:
    device_config = Tasmota()
    device_config.configuration.url = url
    dev = Device(device_config)
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].component_descriptor.configuration_factory()
    else:
        raise Exception(
            "illegal component type " + component_type + ". Allowed values: " +
            ','.join(COMPONENT_TYPE_TO_MODULE.keys())
        )
    component_config.id = num
    dev.add_component(component_config)

    dev.update()


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Tasmota)
