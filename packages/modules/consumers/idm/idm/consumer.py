#!/usr/bin/env python3
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.idm.idm.config import Idm

log = logging.getLogger(__name__)


def create_consumer(config: Idm):
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
        if config.configuration.version == 1:
            power = client.read_holding_registers(4122, ModbusDataType.FLOAT_32,
                                                  unit=config.configuration.modbus_id) * 1000
        else:
            power = client.read_input_registers(4122, ModbusDataType.FLOAT_32,
                                                unit=config.configuration.modbus_id) * 100
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_limit(power_limit: float) -> None:
        nonlocal client
        # if config.configuration.send_import:

        # client.write_registers(1000, power_limit, unit=config.configuration.modbus_id)
    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                module_error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Idm)
