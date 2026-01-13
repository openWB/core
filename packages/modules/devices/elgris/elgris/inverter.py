#!/usr/bin/env python3
from typing import Any, TypedDict

from modules.common.component_state import InverterState
from modules.devices.elgris.elgris.elgris import Elgris
from modules.common.store._inverter import get_inverter_value_store
from modules.devices.elgris.elgris.config import ElgrisInverterSetup
from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState


class KwargsDict(TypedDict):
    tcp_client: modbus.ModbusTcpClient_
    modbus_id: int


class ElgrisInverter(AbstractInverter):
    def __init__(self, component_config: ElgrisInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.elgris = Elgris(self.__modbus_id, self.__tcp_client, self.fault_state)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)

    def update(self):
        with self.__tcp_client:
            counter_state = self.elgris.get_counter_state()
        inverter_state = InverterState(
            exported=counter_state.exported,
            imported=counter_state.imported,
            power=counter_state.power,
            currents=counter_state.currents,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ElgrisInverterSetup)
