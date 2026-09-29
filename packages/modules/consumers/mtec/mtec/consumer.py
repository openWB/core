#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.mtec.mtec.config import Mtec

log = logging.getLogger(__name__)


def create_consumer(config: Mtec):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def update() -> ConsumerState:
        # Reg 707: elektrische Leistungsaufnahme [W]
        power = client.read_holding_registers(707, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 1000: PV-Überschussleistung [W]
        value = 0 if power_limit is None else max(round(power_limit), 0)
        client.write_register(1000, value, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Mtec)
