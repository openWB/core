#!/usr/bin/env python3
import logging
from typing import Iterable, Optional, Union, List

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.sample_request_by_device import bat, counter, inverter
from modules.devices.sample_request_by_device.bat import SampleBat
from modules.devices.sample_request_by_device.config import Sample, SampleConfiguration, SampleBatSetup, SampleCounterSetup, SampleInverterSetup
from modules.devices.sample_request_by_device.counter import SampleCounter
from modules.devices.sample_request_by_device.inverter import SampleInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sample):
    def create_bat_component(component_config: SampleBatSetup):
        return SampleBat(device_config.id, component_config)

    def create_counter_component(component_config: SampleCounterSetup):
        return SampleCounter(device_config.id, component_config)

    def create_inverter_component(component_config: SampleInverterSetup):
        return SampleInverter(device_config.id, component_config)

    def update_components(components: Iterable[Union[SampleBat, SampleCounter, SampleInverter]]):
        response = req.get_http_session().get(device_config.configuration.ip_address, timeout=5).json()
        for component in components:
            component.update(response)

    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


COMPONENT_TYPE_TO_MODULE = {
    "bat": bat,
    "counter": counter,
    "inverter": inverter
}


def read_legacy(component_type: str, ip_address: str, id: int, num: Optional[int]) -> None:
    device_config = Sample(configuration=SampleConfiguration(ip_address=ip_address, id=id))
    dev = create_device(device_config)
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].component_descriptor.configuration_factory()
    else:
        raise Exception(
            "illegal component type " + component_type + ". Allowed values: " +
            ','.join(COMPONENT_TYPE_TO_MODULE.keys())
        )
    component_config.id = num
    dev.add_component(component_config)

    log.debug('Sample IP-Adresse: ' + ip_address)
    log.debug('Sample ID: ' + str(id))

    dev.update()
    # Hier kann es notwendig sein, für 1.9 eine eigene Update-Methode zu implemenitieren, die die Werte wie benötigt miteinander verrechnet.
    # Hier muss auch bei Hybrid-Systemen die Speicher-und PV-Leistung verrechnet werden.


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Sample)
