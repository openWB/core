#!/usr/bin/env python3
import logging

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, IndependentComponentUpdater
from modules.devices.sample_request_by_component.bat import SampleBat
from modules.devices.sample_request_by_component.config import Sample, SampleBatSetup, SampleCounterSetup, SampleInverterSetup
from modules.devices.sample_request_by_component.counter import SampleCounter
from modules.devices.sample_request_by_component.inverter import SampleInverter

log = logging.getLogger(__name__)


def create_device(device_config: Sample):
    session = None

    def create_bat_component(component_config: SampleBatSetup):
        return SampleBat(component_config,
                         device_id=device_config.id,
                         ip_address=device_config.configuration.ip_address)

    def create_counter_component(component_config: SampleCounterSetup):
        return SampleCounter(component_config,
                             device_id=device_config.id,
                             ip_address=device_config.configuration.ip_address)

    def create_inverter_component(component_config: SampleInverterSetup):
        return SampleInverter(component_config,
                              device_id=device_config.id,
                              ip_address=device_config.configuration.ip_address)

    def initializer():
        nonlocal session
        session = req.get_http_session()

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update(session))
    )


device_descriptor = DeviceDescriptor(configuration_factory=Sample)
