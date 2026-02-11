#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.nibe.nibe_s_series.config import Nibe

log = logging.getLogger(__name__)


def create_consumer(config: Nibe):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, 502)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal client, sim_counter
        power = client.read_input_registers(2166, ModbusDataType.UINT_32,
                                            unit=config.configuration.modbus_id)  # / 10 lt Doku?
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=Nibe)
