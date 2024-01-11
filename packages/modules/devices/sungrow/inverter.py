#!/usr/bin/env python3
from typing import Dict, Union

from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.sungrow.config import SungrowInverterSetup, Sungrow
from modules.devices.sungrow.version import Version


class SungrowInverter:
    def __init__(self,
                 device_config: Union[Dict, Sungrow],
                 component_config: Union[Dict, SungrowInverterSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.device_config = device_config
        self.component_config = dataclass_from_dict(SungrowInverterSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> float:
        unit = self.device_config.configuration.modbus_id

        if self.device_config.configuration.version == Version.SH:
            power = self.__tcp_client.read_input_registers(5030, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -1
            exported = self.__tcp_client.read_input_registers(5660, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, unit=unit) * 100
        elif self.device_config.configuration.version == Version.SH_winet_dongle:
            # Not recommended to use the SH WiNet-S-Dongle, but if, this is the most accurate data:
            power = self.__tcp_client.read_input_registers(5016, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -1
            _, exported = self.sim_counter.sim_count(power)
        else:
            power = self.__tcp_client.read_input_registers(5030, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -1
            exported = self.__tcp_client.read_input_registers(5143, ModbusDataType.UINT_32,
                                                              wordorder=Endian.Little, unit=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)
        return power


component_descriptor = ComponentDescriptor(configuration_factory=SungrowInverterSetup)
