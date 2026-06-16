#!/usr/bin/env python3
from enum import IntEnum
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.askoma.askoheat.config import SampleConsumer

log = logging.getLogger(__name__)


class Register(IntEnum):
    POWER = 1000
    TEMP0 = 1001
    TEMP1 = 1030
    TEMP2 = 1031
    STATUS = 1003


REG_MAPPING = (
    (Register.POWER, [ModbusDataType.INT_16]),
    (Register.TEMP0, [ModbusDataType.INT_16]),
    (Register.TEMP1, [ModbusDataType.INT_16]),
    (Register.TEMP2, [ModbusDataType.INT_16]),
    (Register.STATUS, ModbusDataType.INT_16),
)


def create_consumer(config: SampleConsumer):
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
        resp = client.read_holding_registers_bulk(
            Register.POWER, 35, mapping=REG_MAPPING, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(resp[Register.POWER])
        return ConsumerState(
            power=resp[Register.POWER],
            imported=imported,
            exported=exported,
            temperatures=[resp[Register.TEMP0]/10, resp[Register.TEMP1]/10, resp[Register.TEMP2]/10]
        )

    def set_limit(power_limit: float) -> None:
        nonlocal client
        client.write_registers(1000, power_limit, unit=config.configuration.modbus_id)

    # ODER

    def switch_on() -> None:
        nonlocal client
        client.write_registers(1000, 1, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        nonlocal client
        client.write_registers(1000, 0, unit=config.configuration.modbus_id)
    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=SampleConsumer)
