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
from modules.consumers.lambda_.lambda_.config import Lambda

log = logging.getLogger(__name__)


def create_consumer(config: Lambda):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def send_values() -> None:
        # Sendet den aktuellen PV-Überschuss an den Lambda E-Manager (Register 0102,
        # Modbus-Protokoll 1.0, Kap. 3.2 und 4.3). Der EVU-Zähler in openWB ist positiv bei
        # Bezug, negativ bei Einspeisung -> Vorzeichen drehen und auf 0 begrenzen, um den
        # Überschuss als positiven Wert zu erhalten. Der E-Manager muss zusätzlich einmalig
        # auf der Wärmepumpe selbst auf Datenquelle "Modbus Client" umgestellt werden (Kap. 4.3),
        # das kann openWB nicht per Modbus setzen.
        grid_power = data.data.counter_all_data.get_evu_counter().data.get.power
        pv_surplus = max(-grid_power, 0)
        client.write_register(102, pv_surplus, wordorder=Endian.Little, unit=config.configuration.modbus_id)

    def update() -> ConsumerState:
        power = client.read_holding_registers(103, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
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
                                update=update,)


device_descriptor = DeviceDescriptor(configuration_factory=Lambda)
