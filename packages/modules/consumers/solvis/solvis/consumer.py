#!/usr/bin/env python3
from typing import Optional
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.consumers.solvis.solvis.config import SolvisHeatPump


def create_consumer(config: SolvisHeatPump):
    client: Optional[ModbusTcpClient_] = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        power = client.read_input_registers(33545, ModbusDataType.INT_16, unit=config.configuration.modbus_id) * 100
        return ConsumerState(power=power)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=SolvisHeatPump)
