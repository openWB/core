#!/usr/bin/env python3
import logging

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, IndependentComponentUpdater
from modules.devices.mystrom.mystrom.config import Mystrom, MystromCounterSetup
from modules.devices.mystrom.mystrom.counter import MystromCounter

log = logging.getLogger(__name__)


def create_device(device_config: Mystrom):
    session = None

    def create_counter_component(component_config: MystromCounterSetup):
        return MystromCounter(component_config,
                              device_id=device_config.id,
                              ip_address=device_config.configuration.ip_address)

    def initializer():
        nonlocal session
        session = req.get_http_session()

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            counter=create_counter_component,
        ),
        component_updater=IndependentComponentUpdater(lambda component: component.update(session))
    )


device_descriptor = DeviceDescriptor(configuration_factory=Mystrom)
