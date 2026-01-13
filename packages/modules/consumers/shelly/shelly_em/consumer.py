#!/usr/bin/env python3
import logging
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.devices.shelly.shelly.device import create_device
from modules.consumers.shelly.shelly_em.config import ShellyEMConfiguration, ShellyEM
from modules.devices.shelly.shelly.config import (ShellyConfiguration as ShellyDeviceConfiguration,
                                                  Shelly as ShellyDevice,
                                                  ShellyCounterSetup as ShellyDeviceCounterSetup)

log = logging.getLogger(__name__)


class ShellyConsumer(AbstractConsumer):
    def __init__(self, config: ShellyEM) -> None:
        self.config = config

    def initializer(self):
        self.device = create_device(device_config=ShellyDevice(
            configuration=ShellyDeviceConfiguration(
                ip_address=self.config.configuration.ip_address,
                factor=self.config.configuration.factor,
                phase=self.config.configuration.phase),),
            id=self.config.id)
        self.device.create_counter_component(component_config=ShellyDeviceCounterSetup(type="consumer_counter"))

    def error_handler(self) -> None:
        self.initializer()

    def update(self) -> None:
        self.device.update()


def create_consumer(config: ShellyEMConfiguration):
    return ConfigurableConsumer(ShellyConsumer(config))


device_descriptor = DeviceDescriptor(configuration_factory=ShellyEM)
