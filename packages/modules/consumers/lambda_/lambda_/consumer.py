#!/usr/bin/env python3
from pymodbus.constants import Endian
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.lambda_.lambda_.config import Lambda

log = logging.getLogger(__name__)


def create_consumer(config: Lambda):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal client, sim_counter
        client.read_holding_registers(103, ModbusDataType.INT16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_limit(power_limit: float) -> None:
        nonlocal client
        client.write_register(102, max(power_limit * config.configuration.sign, 0), wordorder=Endian.Little, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Lambda)
