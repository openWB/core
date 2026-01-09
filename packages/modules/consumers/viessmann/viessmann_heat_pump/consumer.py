#!/usr/bin/env python3
import logging
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusTcpClient_
from modules.consumers.viessmann.viessmann_heat_pump.config import ViessmannConfiguration, ViessmannHeatPump

log = logging.getLogger(__name__)


class ViessmannHeatPumpConsumer(AbstractConsumer):
    def __init__(self, config: ViessmannConfiguration) -> None:
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


def create_consumer(config: ViessmannConfiguration):
    return ConfigurableConsumer(ViessmannHeatPumpConsumer(config))


device_descriptor = DeviceDescriptor(configuration_factory=ViessmannHeatPump)
