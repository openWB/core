#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.lg_therma.lg_therma.config import LgTherma

log = logging.getLogger(__name__)


def create_consumer(config: LgTherma):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def switch_on() -> None:
        # Reg 9: Energy State, 3 = Ein-Empfehlung (Boost)
        client.write_register(9, 3, data_type=ModbusDataType.UINT_16, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        # Reg 9: Energy State, 2 = Normalbetrieb
        client.write_register(9, 2, data_type=ModbusDataType.UINT_16, unit=config.configuration.modbus_id)

    def update() -> ConsumerState:
        # Reg 35: elektrische Leistungsaufnahme [W]
        power = client.read_input_registers(35, ModbusDataType.UINT_16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=LgTherma)
