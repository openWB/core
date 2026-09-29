#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.consumers.mitsubishi.mitsubishi_modbus.config import MitsubishiModbus

log = logging.getLogger(__name__)


def create_consumer(config: MitsubishiModbus):
    client: Optional[ModbusTcpClient_] = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)

    def switch_on() -> None:
        # Reg 0: AC unit On/Off, 1 = On
        client.write_register(0, 1, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        # Reg 0: AC unit On/Off, 0 = Off
        client.write_register(0, 0, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    # Keine update()-Funktion: das Intesis-Interface stellt keine Leistungsmessung zur Verfügung.
    # Wer den Verbrauch erfassen will, braucht eine separate Leistungsmessung (zB
    # Zwischenzähler/Smart-Plug), die diesem Verbraucher zugeordnet wird.
    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=MitsubishiModbus)
