#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.weishaupt.weishaupt_wwp.config import Weishaupt

log = logging.getLogger(__name__)


def create_consumer(config: Weishaupt):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def update() -> ConsumerState:
        # Reg 33126: El. Leistungsaufnahme [W]
        power = client.read_input_registers(33126, ModbusDataType.UINT_16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 40002: SollwertPV [W], 0 gibt die Regelung an die Wärmepumpe zurück (0..65535,
        # daher clamp statt negativer Werte).
        value = 0 if power_limit is None else min(max(round(power_limit), 0), 65535)
        client.write_register(40002, value, data_type=ModbusDataType.UINT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Weishaupt)
