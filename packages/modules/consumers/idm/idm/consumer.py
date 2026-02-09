#!/usr/bin/env python3
from pymodbus.constants import Endian
import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
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
        sim_counter = SimCounterConsumer(config.id, config.type)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        nonlocal client, sim_counter
        if config.configuration.version == 1:
            power = client.read_holding_registers(4122, ModbusDataType.FLOAT_32,
                                                  unit=config.configuration.modbus_id)
        else:
            power = client.read_input_registers(4122, ModbusDataType.FLOAT_32,
                                                unit=config.configuration.modbus_id)
        power *= 100
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_limit(power_limit: float) -> None:
        # braucht man Reg 78? der Wärmepumpe kann es doch egal sein, wie viel PV-Leistung vom Dach kommt,
        # vlt soll die anderweitig genutzt werden
        # <option value="UP" data-option="UP">Überschuss als positive Zahl übertragen, Bezug negativ</option>
        # <option value="UZ" data-option="UZ">Überschuss als positive Zahl übertragen, Bezug als 0</option>
        # muss man unterscheiden, ob Bezug als negative Zahl oder null übertragen werden soll. Die Wärmepumpe kann
        # den Bezug ja nicht kompensieren. Bei 0W oder 500W Bezug soll das Verhalten gleich sein (Wärmepumpe nur 
        # nach Bedarf einschalten, Eigensteuerung)
        nonlocal client
        # if config.configuration.send_import:
        #     power_limit = min(power_limit, MAX_VALUE_UINT32)
        #     power_limit = max(power_limit, 0)
        # else:
        #     power_limit = min(power_limit, MAX_VALUE_INT16)
        #     power_limit = max(power_limit, MIN_VALUE_INT16)

        client.write_register(74, max(power_limit, 0), wordorder=Endian.Little, unit=config.configuration.modbus_id)
    return ConfigurableConsumer(consumer_config=config,
                                module_initializer=initializer,
                                module_error_handler=error_handler,
                                update=update,
                                set_power_limit=set_limit,)


device_descriptor = DeviceDescriptor(configuration_factory=Idm)
