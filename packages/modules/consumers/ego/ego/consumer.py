#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common.abstract_consumer import CurrentValues
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.ego.ego.config import Ego

log = logging.getLogger(__name__)


def create_consumer(config: Ego):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def send_values(values: CurrentValues) -> None:
        unit = config.configuration.modbus_id
        # Reg 4864 = -1: Heizstab nutzt selbst Reg 4865 (HomeTotalPower) zur Regelung.
        client.write_register(4864, -1, data_type=ModbusDataType.INT_16, unit=unit)
        # Reg 4865/4866: Netzsaldo, negativ = Überschuss (gleiche Konvention wie evu_power).
        client.write_register(4865, round(values.evu_power), data_type=ModbusDataType.INT_32, unit=unit)

    def update() -> ConsumerState:
        unit = config.configuration.modbus_id
        status = client.read_holding_registers(5128, ModbusDataType.UINT_16, unit=unit)
        power = 0
        if status & 0x01:
            power += client.read_holding_registers(4096, ModbusDataType.UINT_16, unit=unit)
        if status & 0x02:
            power += client.read_holding_registers(4128, ModbusDataType.UINT_16, unit=unit)
        if status & 0x04:
            power += client.read_holding_registers(4160, ModbusDataType.UINT_16, unit=unit)
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # Reg 4864: gewünschte Leistung [W], bestmöglich auf die 500/1000/2000W-Relais verteilt.
        value = 0 if power_limit is None else max(round(power_limit), 0)
        client.write_register(4864, value, data_type=ModbusDataType.INT_16, unit=config.configuration.modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                send_values=send_values,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Ego)
