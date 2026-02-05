#!/usr/bin/env python3
from enum import IntEnum
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.my_pv.elwa_e.config import Acthor

log = logging.getLogger(__name__)


class Register(IntEnum):
    POWER = 1000
    TEMP0 = 1001
    STATUS = 1003


REG_MAPPING = (
    (Register.POWER, [ModbusDataType.INT_16]),
    (Register.TEMP0, [ModbusDataType.INT_16]),
    (Register.STATUS, ModbusDataType.INT_16),
)

STATUS = {
    2: "Heat",
    3: "Standby",
    4: "Boost heat",
    5: "Heat finished",
    9: "Setup",
    201: "Error Overtemp Fuse blown",
    202: "Error Overtemp measured",
    203: "Error Overtemp Electronics",
    204: "Error Hardware Fault",
    205: "Error Temp Sensor"
}


def create_consumer(config: Acthor):
    client = None
    fuse = 1
    power = 0
    sim_counter = None
    status = None

    def initializer():
        nonlocal client, fuse, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        fuse = client.read_input_registers(1014, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        sim_counter = SimCounterConsumer(config.id, config.type)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal client, sim_counter, status
        resp = client.read_holding_registers_bulk(
            Register.POWER, 4, mapping=REG_MAPPING, unit=config.configuration.modbus_id)
        power = resp[Register.POWER]
        status = resp[Register.STATUS]
        if status > 200:
            raise Exception(f"Elwa-E meldet einen Fehler-Status: {STATUS.get(status, 'Unknown status')}")
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported,
            temperatures=[resp[Register.TEMP0]/10]
        )

    def set_limit(power_limit: float) -> None:
        nonlocal client, fuse, power, status
        if status == 4:
            log.debug("Elwa-E im Boost-Heat Modus, keine Leistungsvorgabe möglich")
            return
        if power_limit < power:
            power_limit = power + (power - power_limit) * fuse
        power_limit = min(power_limit, 4000)
        power_limit = min(power_limit, 0)

        client.write_registers(1000, power_limit, unit=config.configuration.modbus_id)
    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                module_error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Acthor)
