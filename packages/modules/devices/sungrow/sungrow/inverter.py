#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.sungrow.sungrow.config import SungrowInverterSetup, Sungrow
from modules.devices.sungrow.sungrow.version import Version


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_config: Sungrow


class SungrowInverter(AbstractInverter):
    def __init__(self, component_config: SungrowInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: Sungrow = self.kwargs['device_config']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> float:
        unit = self.device_config.configuration.modbus_id

        if self.device_config.configuration.version in (Version.SH, Version.SH_winet_dongle):
            power = self.__tcp_client.read_input_registers(13033, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -1
            dc_power = self.__tcp_client.read_input_registers(5016, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, unit=unit) * -1

            current_L1 = self.__tcp_client.read_input_registers(13030, ModbusDataType.INT_16, unit=unit) * -0.1
            current_L2 = self.__tcp_client.read_input_registers(13031, ModbusDataType.INT_16, unit=unit) * -0.1
            current_L3 = self.__tcp_client.read_input_registers(13032, ModbusDataType.INT_16, unit=unit) * -0.1
            currents = [current_L1, current_L2, current_L3]
        else:
            power = self.__tcp_client.read_input_registers(5030, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -1
            dc_power = self.__tcp_client.read_input_registers(5016, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, unit=unit) * -1

            current_L1 = self.__tcp_client.read_input_registers(5021, ModbusDataType.UINT_16, unit=unit) * -0.1
            current_L2 = self.__tcp_client.read_input_registers(5022, ModbusDataType.UINT_16, unit=unit) * -0.1
            current_L3 = self.__tcp_client.read_input_registers(5023, ModbusDataType.UINT_16, unit=unit) * -0.1
            currents = [current_L1, current_L2, current_L3]

        imported, exported = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            dc_power=dc_power,
            currents=currents,
            imported=imported,
            exported=exported
        )
        self.store.set(inverter_state)
        return power


component_descriptor = ComponentDescriptor(configuration_factory=SungrowInverterSetup)
