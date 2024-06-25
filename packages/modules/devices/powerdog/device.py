#!/usr/bin/env python3
import logging
from typing import Dict, Union, Optional, List

from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common import modbus
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import MultiComponentUpdateContext, SingleComponentUpdateContext
from modules.devices.powerdog import counter
from modules.devices.powerdog import inverter
from modules.devices.powerdog.config import Powerdog, PowerdogConfiguration, PowerdogCounterSetup, PowerdogInverterSetup

log = logging.getLogger(__name__)


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "counter": counter.PowerdogCounter,
        "inverter": inverter.PowerdogInverter
    }

    def __init__(self, device_config: Union[Dict, Powerdog]) -> None:
        self.components = {}  # type: Dict[str, Union[counter.PowerdogCounter, inverter.PowerdogInverter]]
        try:
            self.device_config = dataclass_from_dict(Powerdog, device_config)
            self.client = modbus.ModbusTcpClient_(
                self.device_config.configuration.ip_address, self.device_config.configuration.port)
        except Exception:
            log.exception("Fehler im Modul "+self.device_config.name)

    def add_component(self, component_config: Union[Dict, PowerdogCounterSetup, PowerdogInverterSetup]) -> None:
        if isinstance(component_config, Dict):
            component_type = component_config["type"]
        else:
            component_type = component_config.type
        component_config = dataclass_from_dict(COMPONENT_TYPE_TO_MODULE[
            component_type].component_descriptor.configuration_factory, component_config)
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config.id)] = (
                self.COMPONENT_TYPE_TO_CLASS[component_type](
                    self.device_config.id, component_config, self.client,
                    self.device_config.configuration.modbus_id))
        else:
            raise Exception(
                "illegal component type " + component_type + ". Allowed values: " +
                ','.join(self.COMPONENT_TYPE_TO_CLASS.keys())
            )

    def update(self) -> None:
        log.debug("Start device reading " + str(self.components))
        with MultiComponentUpdateContext(self.components):
            if len(self.components) == 1:
                for component in self.components:
                    if isinstance(self.components[component], inverter.PowerdogInverter):
                        with SingleComponentUpdateContext(self.components[component].fault_state):
                            self.components[component].update()
                    else:
                        raise Exception(
                            "Wenn ein EVU-Zähler konfiguriert wurde, muss immer auch ein WR konfiguriert sein.")
            elif len(self.components) == 2:
                for component in self.components:
                    if isinstance(self.components[component], inverter.PowerdogInverter):
                        inverter_power = self.components[component].update()
                        break
                else:
                    inverter_power = 0
                for component in self.components:
                    if isinstance(self.components[component], counter.PowerdogCounter):
                        self.components[component].update(inverter_power)
            else:
                log.warning(
                    self.device_config.name +
                    ": Es konnten keine Werte gelesen werden, da noch keine oder zu viele Komponenten konfiguriert "
                    + "wurden."
                )


COMPONENT_TYPE_TO_MODULE = {
    "counter": counter,
    "inverter": inverter
}


def read_legacy(component_type: str, ip_address: str, num: Optional[int] = None) -> None:
    dev = Device(Powerdog(configuration=PowerdogConfiguration(ip_address=ip_address)))
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].component_descriptor.configuration_factory()
    else:
        raise Exception(
            "illegal component type " + component_type + ". Allowed values: " +
            ','.join(COMPONENT_TYPE_TO_MODULE.keys())
        )
    component_config.id = num
    dev.add_component(component_config)

    # Wenn der EVU-Zähler ausgelesen werden soll, wird auch noch der Inverter benötigt.
    if component_type in COMPONENT_TYPE_TO_MODULE and component_type == "counter":
        inverter_config = PowerdogInverterSetup()
        inverter_config.id = 1
        dev.add_component(inverter_config)

    log.debug('Powerdog IP-Adresse: ' + ip_address)

    dev.update()


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Powerdog)
