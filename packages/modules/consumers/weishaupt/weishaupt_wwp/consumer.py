#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.consumers.weishaupt.weishaupt_wwp.config import Weishaupt

log = logging.getLogger(__name__)


def create_consumer(config: Weishaupt):
    client: Optional[ModbusTcpClient_] = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 40002: SollwertPV [W], 0 gibt die Regelung an die Wärmepumpe zurück (0..65535,
        # daher clamp statt negativer Werte).
        value = 0 if power_limit is None else min(max(round(power_limit), 0), 65535)
        client.write_register(40002, value, data_type=ModbusDataType.UINT_16, unit=config.configuration.modbus_id)

    # Keine update()-Funktion: die Datenpunktliste (83807301) enthält keine elektrische
    # Leistungsaufnahme, nur Leistungsanforderung in % (Reg 33103). Wer den Verbrauch erfassen
    # will, braucht eine separate Leistungsmessung (zB Zwischenzähler/Smart-Plug).
    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Weishaupt)
