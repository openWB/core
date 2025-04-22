#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_inverter_value_store
from modules.devices.kaco.kaco_tx.config import KacoInverterSetup
from modules.devices.kaco.kaco_tx.scale import create_scaled_reader


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_
    device_id: int


class KacoInverter(AbstractInverter):
    def __init__(self,
                 component_config: KacoInverterSetup,
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self._read_scaled_int16 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.INT_16
        )
        self._read_scaled_int32 = create_scaled_reader(
            self.__tcp_client, self.component_config.configuration.modbus_id, ModbusDataType.INT_32
        )

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self):
        # 40084     | Total AC Power         | int16
        # 40085     | AC Power scale factor  | sunssf
        power = self._read_scaled_int16(40084, 1)[0] * -1

        # 40094     | AC Energy              | acc32
        # 40096     | AC Energy scale factor | sunssf
        exported = self._read_scaled_int32(40094, 1)[0]

        return InverterState(
            power=power,
            exported=exported
        )


component_descriptor = ComponentDescriptor(configuration_factory=KacoInverterSetup)
