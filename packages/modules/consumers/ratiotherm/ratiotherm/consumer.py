#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.ratiotherm.ratiotherm.config import Ratiotherm

log = logging.getLogger(__name__)


def create_consumer(config: Ratiotherm):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def set_limit(power_limit: float) -> None:
        nonlocal client
        # Absturz bei negativen Zahlen
        client.write_register(100, max(power_limit, 0), ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Ratiotherm)
