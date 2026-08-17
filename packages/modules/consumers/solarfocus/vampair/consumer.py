#!/usr/bin/env python3
from modules.common.abstract_consumer import CurrentValues
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.solarfocus.vampair.config import VampairHeatPump


def create_consumer(config: VampairHeatPump):
    client = None
    sim_counter = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def update() -> ConsumerState:
        power = client.read_holding_registers(2322, ModbusDataType.INT_16, unit=config.configuration.modbus_id)
        imported, exported = sim_counter.sim_count(power)
        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_limit(power_limit: float) -> None:
        # Elektrische Sollleistung HEMS (PV)
        client.write_register(33415, power_limit, unit=config.configuration.modbus_id)
        client.write_register(33409, power_limit * -1, unit=config.configuration.modbus_id)

    def send_values(values: CurrentValues) -> None:
        client.write_register(33408, values.pv_power * -1, unit=config.configuration.modbus_id)
        client.write_register(33409, values.evu_power * -1, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                update=update,
                                set_limit=set_limit,
                                send_values=send_values)


device_descriptor = DeviceDescriptor(configuration_factory=VampairHeatPump)
