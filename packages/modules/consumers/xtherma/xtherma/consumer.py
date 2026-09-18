#!/usr/bin/env python3
import logging
from typing import Optional

from helpermodules import timecheck
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.xtherma.xtherma.config import Xtherma

log = logging.getLogger(__name__)


def create_consumer(config: Xtherma):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None
    last_write: Optional[float] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def update() -> ConsumerState:
        # Reg 177 (in_total): elektrische Leistungsaufnahme, Auflösung 10W
        power = client.read_holding_registers(
            177, ModbusDataType.UINT_16, unit=config.configuration.modbus_id) * 10
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 70/71 dürfen laut Xtherma-Protokoll höchstens 1x/min beschrieben werden.
        nonlocal last_write
        if last_write is not None and timecheck.check_timestamp(last_write, 60):
            return
        last_write = timecheck.create_timestamp()
        unit = config.configuration.modbus_id
        if power_limit is None:
            client.write_register(70, 0, data_type=ModbusDataType.UINT_16, unit=unit)
        else:
            # Reg 71: Überschuss [W], 0..100000
            client.write_register(
                71, min(max(round(power_limit), 0), 100000), data_type=ModbusDataType.UINT_16, unit=unit)
            client.write_register(70, 1, data_type=ModbusDataType.UINT_16, unit=unit)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Xtherma)
