#!/usr/bin/env python3
import logging
from typing import Optional
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.askoma.askoheat.config import Askoheat

log = logging.getLogger(__name__)


def create_consumer(config: Askoheat):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        power = client.read_input_registers(110, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            temperatures=[client.read_input_registers(638, ModbusDataType.INT_16, unit=config.configuration.modbus_id)]
        )

    def set_power_limit(power_limit: float, data: SetLimitData) -> None:
        client.write_register(201, power_limit, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                set_power_limit=set_power_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Askoheat)
