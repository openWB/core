#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.ampere.ampere.config import AmpereInverterSetup


class AmpereInverter(AbstractInverter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, AmpereInverterSetup],
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(AmpereInverterSetup, component_config)
        self.modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        pv1_power = client.read_holding_registers(519, ModbusDataType.INT_16, unit=self.modbus_id) * -1
        pv2_power = client.read_holding_registers(522, ModbusDataType.INT_16, unit=self.modbus_id) * -1

        power = pv1_power + pv2_power

        _, exported = self.sim_counter.sim_count(power)
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=AmpereInverterSetup)
