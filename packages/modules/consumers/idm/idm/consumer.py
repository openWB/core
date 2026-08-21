#!/usr/bin/env python3
from pymodbus.constants import Endian
import logging

from modules.common.abstract_consumer import CurrentValues
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.idm.idm.config import Idm

log = logging.getLogger(__name__)


def create_consumer(config: Idm):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def send_values(values: CurrentValues) -> None:
        # Sendet die aktuellen Systemwerte an die IDM Navigator 2.0-Regelung über die
        # Gebäudeleittechnik/Smartfox-Schnittstelle (Modbus TCP). IDM unterstützt keine
        # direkte Leistungsvorgabe für die WP - die Regelung berechnet ihre Überschuss- und
        # Speicherstrategie selbst anhand dieser Werte. Wird vom Core automatisch aufgerufen,
        # solange dieser Verbraucher als ConsumerUsage.SELF_CONTROLLED konfiguriert ist.
        # Register-Layout siehe IDM "Gebäudeleittechnik-Smartfox.pdf", Kap. 2.2.5.1
        modbus_id = config.configuration.modbus_id

        # values.pv_power kommt roh aus process.py (negativ während Produktion, gleiche
        # Konvention wie beim EVU-Zähler) -> Vorzeichen drehen und auf 0 begrenzen, um die
        # reine Erzeugung zu erhalten
        pv_power = max(-values.pv_power, 0)
        # Ladeleistung mit einrechnen, da diese sonst fälschlich als freier Überschuss an die
        # WP gemeldet würde, obwohl sie bereits von einer Fahrzeugladung verbraucht wird
        surplus = max(pv_power - values.home_consumption - values.cp_power, 0)
        battery_soc = int(values.bat_soc) if values.bat_soc is not None else -1

        # Reg 74: Aktueller PV-Überschuss [kW]
        client.write_register(74, surplus / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 78: Aktuelle PV-Produktion [kW]
        client.write_register(78, pv_power / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 82: Hausverbrauch [kW], Default 0
        client.write_register(82, values.home_consumption / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 84: Batterieentladung [kW], Default 0 (negativ = Ladung)
        client.write_register(84, values.bat_power / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 86: Batteriefüllstand [%], Default -1 (= kein Speicher)
        client.write_register(86, battery_soc, unit=modbus_id)

    def update() -> ConsumerState:
        if config.configuration.version == 1:
            power = client.read_holding_registers(
                4122, ModbusDataType.FLOAT_32, unit=config.configuration.modbus_id)
        else:
            power = client.read_input_registers(
                4122, ModbusDataType.FLOAT_32, unit=config.configuration.modbus_id)
        power *= 100
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_limit(power_limit: float) -> None:
        # Schreibt den von openWB berechneten Überschuss in Register 74 (PV-Überschuss [kW]).
        # Keine echte Leistungsvorgabe - die IDM-Regelung berechnet ihre Strategie selbst anhand dieses Wertes.
        # Hinweis: Dies überschreibt den intern berechneten PV-Überschuss der IDM-Regelung und kann
        # die PV-Eigenverbrauchs-Statistik im IDM-Portal verfälschen.
        client.write_register(74, max(power_limit, 0) / 1000, wordorder=Endian.Little,
                              unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                send_values=send_values,
                                set_power_limit=set_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Idm)
