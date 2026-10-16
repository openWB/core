#!/usr/bin/env python3
import logging
from typing import Optional
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.consumers.nibe.nibe_s_series.config import Nibe

log = logging.getLogger(__name__)


def create_consumer(config: Nibe):
    client: Optional[ModbusTcpClient_] = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, 502)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        power = client.read_input_registers(2166, ModbusDataType.UINT_32,
                                            unit=config.configuration.modbus_id)  # / 10 lt Doku?
        return ConsumerState(power=power)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=Nibe)
