#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.askoma.askoheat.config import Askoheat

log = logging.getLogger(__name__)


def create_consumer(config: Askoheat):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, config.type)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal client, sim_counter
        power = client.read_input_registers(110, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            temperatures=[client.read_input_registers(638, ModbusDataType.INT_16, unit=config.configuration.modbus_id)]
        )

    def set_limit(power_limit: float) -> None:
        nonlocal client
        client.write_registers(201, power_limit, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                module_error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Askoheat)
