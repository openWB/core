#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.kermi.kermi.config import Kermi

log = logging.getLogger(__name__)


def create_consumer(config: Kermi):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def update() -> ConsumerState:
        # Reg 108: aktuelle Leistungsaufnahme, Auflösung 100W
        power = client.read_holding_registers(
            108, ModbusDataType.INT_16, unit=config.configuration.modbus_id) * 100
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 301: PV-Überschussleistung, Auflösung 10W
        value = int(round((0 if power_limit is None else max(power_limit, 0)) / 10))
        client.write_register(301, value, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Kermi)
