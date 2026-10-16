#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.consumers.luxtronik.luxtronik.config import Luxtronik

log = logging.getLogger(__name__)


def create_consumer(config: Luxtronik):
    client: Optional[ModbusTcpClient_] = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)

    def switch_on() -> None:
        unit = config.configuration.modbus_id
        offset = round(config.configuration.boost_offset * 10)
        # Reg 10040: LPC-Modus 0=No-Limit. Reg 10000/10005: Heiz./WW-Modus 2=Offset,
        # Reg 10002/10007: Offset [0.1K].
        client.write_register(10040, 0, data_type=ModbusDataType.UINT_16, unit=unit)
        client.write_register(10000, 2, data_type=ModbusDataType.UINT_16, unit=unit)
        client.write_register(10002, offset, data_type=ModbusDataType.INT_16, unit=unit)
        client.write_register(10005, 2, data_type=ModbusDataType.UINT_16, unit=unit)
        client.write_register(10007, offset, data_type=ModbusDataType.INT_16, unit=unit)

    def switch_off() -> None:
        unit = config.configuration.modbus_id
        client.write_register(10040, 0, data_type=ModbusDataType.UINT_16, unit=unit)
        client.write_register(10000, 0, data_type=ModbusDataType.UINT_16, unit=unit)
        client.write_register(10005, 0, data_type=ModbusDataType.UINT_16, unit=unit)

    def update() -> ConsumerState:
        # Reg 10301: el. Leistungsaufnahme, Auflösung 100W (kW x0.1)
        power = client.read_input_registers(
            10301, ModbusDataType.UINT_16, unit=config.configuration.modbus_id) * 100
        return ConsumerState(power=power)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=Luxtronik)
