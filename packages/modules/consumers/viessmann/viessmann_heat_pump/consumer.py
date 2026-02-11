#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusTcpClient_
from modules.consumers.viessmann.viessmann_heat_pump.config import ViessmannHeatPump


def create_consumer(config: ViessmannHeatPump):
    client = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)

    def error_handler() -> None:
        initializer()

    def switch_on() -> None:
        nonlocal client
        client.write_single_coil(16, True, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        nonlocal client
        client.write_single_coil(16, False, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                switch_on=switch_on,
                                switch_off=switch_off,)


device_descriptor = DeviceDescriptor(configuration_factory=ViessmannHeatPump)
