#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.sungrow.config import SungrowCounterSetup, Sungrow
from modules.devices.sungrow.version import Version


class SungrowCounter:
    def __init__(self,
                 device_config: Union[Dict, Sungrow],
                 component_config: Union[Dict, SungrowCounterSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.device_config = device_config
        self.component_config = dataclass_from_dict(SungrowCounterSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, pv_power: float):
        unit = self.device_config.configuration.modbus_id
        if self.device_config.configuration.version in (Version.SH, Version.SH_winet_dongle):
            power = self.__tcp_client.read_input_registers(13009, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -1
            imported = self.__tcp_client.read_input_registers(13036, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, unit=unit) * 100
            exported = self.__tcp_client.read_input_registers(13045, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, unit=unit) * 100
        else:
            if pv_power != 0:
                power = self.__tcp_client.read_input_registers(5082, ModbusDataType.INT_32,
                                                               wordorder=Endian.Little, unit=unit)
            else:
                power = self.__tcp_client.read_input_registers(5090, ModbusDataType.INT_32,
                                                               wordorder=Endian.Little, unit=unit)
            imported, exported = self.sim_counter.sim_count(power)

        frequency = self.__tcp_client.read_input_registers(5035, ModbusDataType.UINT_16, unit=unit) / 10
        if self.device_config.configuration.version == Version.SH_winet_dongle:
            # On WiNet-S, the frequency accuracy is higher by one place
            frequency /= 10

        power_factor = self.__tcp_client.read_input_registers(5034, ModbusDataType.INT_16, unit=unit) / 1000
        # These are actually output voltages of the inverter:
        voltages = self.__tcp_client.read_input_registers(5018, [ModbusDataType.UINT_16] * 3,
                                                          wordorder=Endian.Little, unit=unit)
        voltages = [voltage / 10 for voltage in voltages]

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            voltages=voltages,
            frequency=frequency,
            power_factors=[power_factor] * 3
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SungrowCounterSetup)
