#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.varta.config import VartaBatModbusSetup


class VartaBatModbus:
    def __init__(self, device_id: int,
                 component_config: VartaBatModbusSetup,
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(VartaBatModbusSetup, component_config)
        self.__modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        self.set_state(self.get_state(client))

    def get_state(self, client: ModbusTcpClient_) -> BatState:
        soc = client.read_holding_registers(1068, ModbusDataType.INT_16, unit=self.__modbus_id)
        power = client.read_holding_registers(1066, ModbusDataType.INT_16, unit=self.__modbus_id)
        return BatState(
            power=power,
            soc=soc,
        )

    def set_state(self, state: BatState) -> None:
        state.imported, state.exported = self.sim_counter.sim_count(state.power)
        self.store.set(state)


component_descriptor = ComponentDescriptor(configuration_factory=VartaBatModbusSetup)
