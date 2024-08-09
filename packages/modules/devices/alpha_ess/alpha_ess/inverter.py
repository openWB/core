#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.devices.alpha_ess.alpha_ess.config import AlphaEssConfiguration, AlphaEssInverterSetup
from modules.common import modbus
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Number
from modules.common.simcount._simcounter import SimCounter
from modules.common.store import get_inverter_value_store


class AlphaEssInverter:
    def __init__(self, device_id: int,
                 component_config: Union[Dict, AlphaEssInverterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 device_config: AlphaEssConfiguration,
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(AlphaEssInverterSetup, component_config)
        self.__tcp_client = tcp_client
        self.__device_config = device_config
        self.__modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        reg_p = self.__version_factory()
        power = self.__get_power(reg_p)

        _, exported = self.sim_counter.sim_count(power)
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)

    def __version_factory(self) -> int:
        if self.__device_config.source == 0 and self.__device_config.version == 0:
            return 0x0012
        else:
            return 0x00A1

    def __get_power(self, reg_p: int) -> Number:
        powers = [
            self.__tcp_client.read_holding_registers(address, ModbusDataType.INT_32, unit=self.__modbus_id)
            for address in [reg_p, 0x041F, 0x0423, 0x0427]
        ]
        powers[0] = abs(powers[0])
        power = sum(powers) * -1
        return power


component_descriptor = ComponentDescriptor(configuration_factory=AlphaEssInverterSetup)
