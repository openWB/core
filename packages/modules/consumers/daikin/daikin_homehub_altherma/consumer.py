#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.daikin.daikin_homehub_altherma.config import DaikinAltherma

log = logging.getLogger(__name__)


def create_consumer(config: DaikinAltherma):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def update() -> ConsumerState:
        # Reg 51: Stromverbrauch Wärmepumpe, Pow16 (raw = kW * 100)
        power = client.read_input_registers(
            50, ModbusDataType.INT_16, unit=config.configuration.modbus_id) * 10
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(power=power, imported=imported, exported=exported)

    def switch_on() -> None:
        # Reg 56: Smart-Grid-Modus, 2 = Empfehlung ein (Boost)
        client.write_register(55, 2, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    def switch_off() -> None:
        # Reg 56: Smart-Grid-Modus, 0 = freier Betrieb (Normal)
        client.write_register(55, 0, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 58: Allgemeine Leistungsbegrenzung, Pow16 (raw = kW * 100), lt. offiziellem
        # Daikin-Referenzhandbuch (EKRHH Installer Reference Guide, Kap. 9.2.1/9.3). Bereich 0..20kW,
        # gilt laut Referenzhandbuch unabhängig vom Smart-Grid-Modus (anders als Reg 57, das nur
        # während der Pufferung im Modus "Empfehlung ein" greift).
        # Die Einheit setzt intern trotzdem eine Untergrenze von 4,5kW für 15 Minuten nach
        # Verdichterstart durch - Werte darunter reduzieren die Leistung in dieser Zeit nicht weiter;
        # echtes Abschalten läuft über switch_off() (Reg 56, Zwangsabschaltung).
        value = 0 if power_limit is None else round(max(power_limit, 0) / 10)
        client.write_register(57, value, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=DaikinAltherma)
