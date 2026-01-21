#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.solvis.solvis.config import SolvisHeatPump


def create_consumer(config: SolvisHeatPump):
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
        power = client.read_input_registers(33545, ModbusDataType.INT_16, unit=config.configuration.modbus_id) * 100
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                module_error_handler=error_handler,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=SolvisHeatPump)
