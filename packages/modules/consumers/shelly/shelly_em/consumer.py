#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.devices.shelly.shelly.device import create_device
from modules.consumers.shelly.shelly_em.config import ShellyEM
from modules.devices.shelly.shelly.config import (ShellyConfiguration as ShellyDeviceConfiguration,
                                                  Shelly as ShellyDevice,
                                                  ShellyCounterSetup as ShellyDeviceCounterSetup)


def create_consumer(config: ShellyEM):
    device = None

    def initializer():
        nonlocal device
        device = create_device(device_config=ShellyDevice(
            configuration=ShellyDeviceConfiguration(
                ip_address=config.configuration.ip_address,
                factor=config.configuration.factor,
                phase=config.configuration.phase),),
            id=config.id)
        device.create_counter_component(component_config=ShellyDeviceCounterSetup(type="consumer_counter"))

    def error_handler() -> None:
        initializer()

    def update() -> None:
        device.update()
    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                module_error_handler=error_handler,
                                update=update,)


device_descriptor = DeviceDescriptor(configuration_factory=ShellyEM)
