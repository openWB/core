#!/usr/bin/env python3
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_counter_value_store
from modules.devices.kostal.kostal_sem.config import KostalSemCounterSetup


class KostalSemCounter(AbstractCounter):
    def __init__(self,
                 component_config: KostalSemCounterSetup,
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:
        self.component_config = component_config
        self.__tcp_client = tcp_client
        self.__modbus_id = modbus_id
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.__tcp_client:
            voltages = [self.__tcp_client.read_holding_registers(
                reg, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.001 for reg in [62, 102, 142]]
            currents = [self.__tcp_client.read_holding_registers(
                reg, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.001 for reg in [60, 100, 140]]
            power_factors = [self.__tcp_client.read_holding_registers(
                reg, ModbusDataType.INT_32, unit=self.__modbus_id) * 0.001 for reg in [64, 104, 144]]
            imported, exported = [val * 0.1 for val in self.__tcp_client.read_holding_registers(
                512, [ModbusDataType.UINT_64]*2, unit=self.__modbus_id)]
            frequency = self.__tcp_client.read_holding_registers(
                26, ModbusDataType.UINT_32, unit=self.__modbus_id) * 0.001

            powers = []
            for reg in [40, 80, 120]:
                powers_temp = self.__tcp_client.read_holding_registers(
                    reg, [ModbusDataType.UINT_32]*2, unit=self.__modbus_id)
                powers.append((powers_temp[0] if powers_temp[0] >= powers_temp[1] else -powers_temp[1]) * 0.1)

            power_temp = self.__tcp_client.read_holding_registers(0, [ModbusDataType.UINT_32]*2, unit=self.__modbus_id)
            power = (power_temp[0] if power_temp[0] >= power_temp[1] else -power_temp[1]) * 0.1

        counter_state = CounterState(
            voltages=voltages,
            currents=currents,
            powers=powers,
            imported=imported,
            exported=exported,
            power=power,
            power_factors=power_factors,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalSemCounterSetup)
