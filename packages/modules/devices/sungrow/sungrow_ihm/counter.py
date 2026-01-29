#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.sungrow.sungrow_ihm.config import SungrowIHM, SungrowIHMCounterSetup


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_config: SungrowIHM


class SungrowIHMCounter(AbstractCounter):
    def __init__(self, component_config: SungrowIHMCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: SungrowIHM = self.kwargs['device_config']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="evu")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))


    def update(self, pv_power: float):
        unit = self.device_config.configuration.modbus_id
        power = self.__tcp_client.read_input_registers(8156, ModbusDataType.INT_32,
                                                       wordorder=Endian.Little, unit=unit) * -10
        
        powers = self.__tcp_client.read_input_registers(8558, [ModbusDataType.UINT_32] * 3,
                                                        wordorder=Endian.Little, unit=unit)
        
        frequency = self.__tcp_client.read_input_registers(8557, ModbusDataType.UINT_16, unit=unit) / 10
        
        voltages = self.__tcp_client.read_input_registers(8554, [ModbusDataType.UINT_16] * 3, 
                                                          wordorder=Endian.Little, unit=unit)

        voltages = [value / 10 for value in voltages]

        imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages,
            frequency=frequency,
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SungrowIHMCounterSetup)
