#!/usr/bin/env python3
from enum import IntEnum
from pymodbus.constants import Endian
import logging

from modules.common.abstract_consumer import CurrentValues
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.lambda_.lambda_.config import Lambda

log = logging.getLogger(__name__)


class Register(IntEnum):
    # Modbus-Protokoll 1.0, Kap. 3.2 und 4.3
    POWER = 103
    GRID_POWER = 102


def create_consumer(config: Lambda):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def send_values(values: CurrentValues) -> None:
        # Sendet die aktuelle EVU-Leistung an den Lambda E-Manager (Modbus-Protokoll 1.0,
        # Kap. 3.2 und 4.3). Der E-Manager muss zusätzlich einmalig auf der Wärmepumpe selbst
        # auf Datenquelle "Modbus Client" umgestellt werden (Kap. 4.3), das kann openWB nicht
        # per Modbus setzen. Wird vom Core automatisch aufgerufen, solange dieser Verbraucher
        # als ConsumerUsage.SELF_CONTROLLED konfiguriert ist.
        client.write_register(Register.GRID_POWER, values.evu_power, wordorder=Endian.Little,
                               unit=config.configuration.modbus_id)

    def update() -> ConsumerState:
        power = client.read_holding_registers(Register.POWER, ModbusDataType.INT_16,
                                                unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                send_values=send_values)


device_descriptor = DeviceDescriptor(configuration_factory=Lambda)
