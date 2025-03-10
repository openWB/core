#!/usr/bin/env python3
import logging
from typing import Iterable, Union

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.sample_request_by_device.bat import SampleBat
from modules.devices.sample_request_by_device.config import Sample, SampleBatSetup, SampleCounterSetup, SampleInverterSetup
from modules.devices.sample_request_by_device.counter import SampleCounter
from modules.devices.sample_request_by_device.inverter import SampleInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sample):
    def create_bat_component(component_config: SampleBatSetup):
        return SampleBat(component_config, device_id=device_config.id)

    def create_counter_component(component_config: SampleCounterSetup):
        return SampleCounter(component_config, device_id=device_config.id)

    def create_inverter_component(component_config: SampleInverterSetup):
        return SampleInverter(component_config, device_id=device_config.id)

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


device_descriptor = DeviceDescriptor(configuration_factory=Sample)
