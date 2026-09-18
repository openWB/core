#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.consumers.daikin.daikin_homehub_air2air.config import Daikin

log = logging.getLogger(__name__)


def create_consumer(config: Daikin):
    client: Optional[ModbusTcpClient_] = None

    def initializer():
        nonlocal client
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)

    def switch_on() -> None:
        # Reg 1000: Smart-Grid-Modus, 2 = Empfehlung ein (Boost)
        client.write_register(1000, 2, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        # Reg 1000: Smart-Grid-Modus, 0 = freier Betrieb (Normal)
        client.write_register(1000, 0, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 1001: Leistungsgrenze für Bedarfssteuerung, Pow16 (raw = kW * 100), lt. offiziellem
        # Daikin-Referenzhandbuch (EKRHH Installer Reference Guide, Kap. 10.2.1/10.2). Bereich 0..20kW.
        # Die Einheit setzt intern trotzdem eine Untergrenze von 40% der Nennleistung der
        # Außeneinheit um - Werte darunter reduzieren die Leistung nicht weiter; echtes Abschalten
        # läuft über switch_off() (Reg 1000, Zwangsabschaltung).
        value = 0 if power_limit is None else round(max(power_limit, 0) / 10)
        client.write_register(1001, value, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    # Keine update()-Funktion: die HomeHub-Anbindung stellt für Air2Air-Geräte keine
    # Leistungsmessung zur Verfügung. Wer den Verbrauch erfassen will, braucht eine separate
    # Leistungsmessung (zB Zwischenzähler/Smart-Plug), die diesem Verbraucher zugeordnet wird.
    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Daikin)
