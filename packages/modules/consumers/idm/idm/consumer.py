#!/usr/bin/env python3
from pymodbus.constants import Endian
import logging

from control import data
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

    def send_values() -> None:
        # Sendet die aktuellen Systemwerte an die IDM Navigator 2.0-Regelung über die
        # Gebäudeleittechnik/Smartfox-Schnittstelle (Modbus TCP). IDM unterstützt keine
        # direkte Leistungsvorgabe für die WP - die Regelung berechnet ihre Überschuss- und
        # Speicherstrategie selbst anhand dieser Werte. Register-Layout siehe IDM
        # "Gebäudeleittechnik-Smartfox.pdf", Kap. 2.2.5.1. Wird nur aufgerufen, wenn
        # config.configuration.send_values aktiviert ist.
        modbus_id = config.configuration.modbus_id

        # pv_all_data.get.power ist negativ, solange PV einspeist (gleiche Konvention wie beim
        # EVU-Zähler) -> Vorzeichen drehen und auf 0 begrenzen, um die reine Erzeugung zu erhalten
        pv_power = max(-data.data.pv_all_data.data.get.power, 0)
        hausverbrauch = data.data.counter_all_data.data.set.home_consumption
        ueberschuss = max(pv_power - hausverbrauch, 0)

        bat = data.data.bat_all_data
        # Get.power ist bei Speichern bereits positiv = Entladung, negativ = Ladung -> passt
        # direkt zur IDM-Registerdefinition "Batterieentladung"
        battery_power = bat.data.get.power if bat.data.config.configured else 0
        battery_soc = bat.data.get.soc if bat.data.config.configured else None

        # Reg 74: Aktueller PV-Überschuss [kW]
        client.write_register(74, ueberschuss / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 78: Aktuelle PV Produktion [kW]
        client.write_register(78, pv_power / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 82: Hausverbrauch [kW], Default 0
        client.write_register(82, hausverbrauch / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 84: Batterieentladung [kW], Default 0 (negativ = Ladung)
        client.write_register(84, battery_power / 1000, wordorder=Endian.Little, unit=modbus_id)
        # Reg 86: Batteriefüllstand [%], Default -1 (= kein Speicher)
        client.write_register(86, int(battery_soc) if battery_soc is not None else -1, unit=modbus_id)

    def update() -> ConsumerState:
        if config.configuration.version == 1:
            power = client.read_holding_registers(
                4122, ModbusDataType.FLOAT_32, unit=config.configuration.modbus_id)
        else:
            power = client.read_input_registers(
                4122, ModbusDataType.FLOAT_32, unit=config.configuration.modbus_id)
        power *= 100
        imported, exported = sim_counter.sim_count(power)

        if config.configuration.send_values:
            send_values()

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=Idm)
