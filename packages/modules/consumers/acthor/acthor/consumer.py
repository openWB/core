#!/usr/bin/env python3
from enum import IntEnum
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.acthor.acthor.config import Acthor

log = logging.getLogger(__name__)


class Register(IntEnum):
    POWER = 1000
    TEMP0 = 1001
    TEMP1 = 1030
    TEMP2 = 1031
    STATUS = 1003


FACTORS = {"9s45": 45000,
           "9s27": 27000,
           "9s18": 18000,
           "9s": 9000,
           "M3": 6000,
           "E2M1": 3500,
           "E2M3": 6500,
           "M1": 3000}
REG_MAPPING = (
    (Register.POWER, [ModbusDataType.INT_16]),
    (Register.TEMP0, [ModbusDataType.INT_16]),
    (Register.TEMP1, [ModbusDataType.INT_16]),
    (Register.TEMP2, [ModbusDataType.INT_16]),
    (Register.STATUS, ModbusDataType.INT_16),
)


def create_consumer(config: Acthor):
    client = None
    sim_counter = None

    def initializer(self):
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, config.type)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal client, sim_counter
        resp = client.read_holding_registers_bulk(
            Register.POWER, 35, mapping=REG_MAPPING, unit=config.configuration.modbus_id)
        power = resp[Register.POWER] * \
            FACTORS.get(config.configuration.model, 9000)/config.configuration.max_power
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            temperatures=[resp[Register.TEMP0]/10, resp[Register.TEMP1]/10, resp[Register.TEMP2]/10]
        )

    def set_limit(power_limit: float) -> None:
        client.write_registers(1000, power_limit, unit=config.configuration.modbus_id)
    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Acthor)
