#!/usr/bin/env python3
import logging
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusTcpClient_
from modules.consumers.shelly.shelly_pm.config import ShellyPM

log = logging.getLogger(__name__)


class ShellyPMConsumer(AbstractConsumer):
    def __init__(self, config: ShellyPM) -> None:
        self.config = config

    def initializer(self):
        self.client = ModbusTcpClient_(self.config.configuration.ip_address, self.config.configuration.port)

    def error_handler(self) -> None:
        self.initializer()

    def update(self) -> None:
        pass

    def switch_on(self) -> None:
        self.client.write_coil(16, True, unit=self.config.configuration.modbus_id)

    def switch_off(self) -> None:
        self.client.write_coil(16, False, unit=self.config.configuration.modbus_id)


def create_consumer(config: ShellyPM):
    return ConfigurableConsumer(ShellyPMConsumer(config))


device_descriptor = DeviceDescriptor(configuration_factory=ShellyPM)
