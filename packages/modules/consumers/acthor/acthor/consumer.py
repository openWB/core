#!/usr/bin/env python3
from enum import IntEnum
import logging
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._factory import get_component_value_store
from modules.consumers.acthor.acthor.config import ActhorConfiguration, Acthor

log = logging.getLogger(__name__)


class Register(IntEnum):
    POWER = 1000
    TEMP0 = 1001
    TEMP1 = 1030
    TEMP2 = 1031
    STATUS = 1003


class ActhorConsumer(AbstractConsumer):
    FACTORS = {"9s45": 45000,
               "9s27": 27000,
               "9s18": 18000,
               "9s": 9000,
               "M3": 6000,
               "E2M1": 3500,
               "E2M3": 6500,
               "M1": 3000,
               "M3": 3000}
    REG_MAPPING = (
        (Register.POWER, [ModbusDataType.INT_16]),
        (Register.TEMP0, [ModbusDataType.INT_16]),
        (Register.TEMP1, [ModbusDataType.INT_16]),
        (Register.TEMP2, [ModbusDataType.INT_16]),
        (Register.STATUS, ModbusDataType.INT_16),
    )

    def __init__(self, config: Acthor) -> None:
        self.config = config

    def initializer(self):
        self.client = ModbusTcpClient_(self.config.configuration.ip_address, self.config.configuration.port)
        self.sim_counter = SimCounter(self.config.id, self.config.id, prefix="bezug")
        self.store = get_component_value_store(self.config.type, self.config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.config))

    def error_handler(self) -> None:
        self.initializer()

    def update(self) -> None:
        resp = self.client.read_holding_registers_bulk(
            Register.POWER, 35, mapping=self.REG_MAPPING, unit=self.config.configuration.modbus_id)
        power = resp[Register.POWER] * \
            self.FACTORS.get(self.config.configuration.model, 9000)/self.config.configuration.max_power
        imported, exported = self.sim_counter.sim_count(power)
        counter_state = ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            temperatures=[resp[Register.TEMP0]/10, resp[Register.TEMP1]/10, resp[Register.TEMP2]/10]
        )

        self.store.set(counter_state)

    def set_limit(self, power_limit: float) -> None:
        self.client.write_registers(1000, power_limit, unit=self.config.configuration.modbus_id)


def create_consumer(config: ActhorConfiguration):
    return ConfigurableConsumer(ActhorConsumer(config))


device_descriptor = DeviceDescriptor(configuration_factory=Acthor)
