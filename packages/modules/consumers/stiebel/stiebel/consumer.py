#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.stiebel.stiebel.config import Stiebel

log = logging.getLogger(__name__)


def create_consumer(config: Stiebel):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def switch_on() -> None:
        nonlocal client
        client.write_register(4001, 1, ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        nonlocal client
        client.write_register(4001, 0, ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                )


device_descriptor = DeviceDescriptor(configuration_factory=Stiebel)
