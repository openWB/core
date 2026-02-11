#!/usr/bin/env python3
from enum import Enum
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.dac.config import Dac

log = logging.getLogger(__name__)


class Model(Enum):
    N4Dac02 = "N4Dac02"
    DA02 = "DA02"
    M120T = "M120T"
    AA02B = "AA02B"


def create_consumer(config: Dac):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def set_limit(power_limit: float) -> None:
        nonlocal client
        if config.configuration.model == Model.N4Dac02 or config.configuration.model == Model.M120T:
            # pwoer_limit -= power
            pass

        # power_limit = max(power_limit, 0)
        # if config.configuration.model == Model.N4Dac02:
        #     client.write_register(1, power_limit * 1000 / max_power, ModbusDataType.INT_16,
        #                           unit=config.configuration.modbus_id)
        # elif config.configuration.model == Model.DA02:
        #     client.write_register(0x01f4, power_limit * 4000 / max_power,
        #                           ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        # elif config.configuration.model == Model.M120T:
        #     #  ausgabe nicht kleiner 0,9V sonst Leistungsregelung der WP aus
        #     power_limit = max(power_limit * 4095 / max_power, 370)
        #     client.write_register(0x01f4, power_limit, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        # elif config.configuration.model == Model.AA02B:
        #     power_limit = max((power_limit * (4095-820) / max_power)+820, 820)
        #     #  ausgabe nicht kleiner 4ma sonst Leistungsregelung der WP aus
        #     client.write_register(0x01f4, power_limit, ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Dac)
