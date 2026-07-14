#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.openwb.openwb_flex_local.config import LocalConsumptionCounterSetup
from modules.devices.openwb.openwb_flex_local.versions import consumption_counter_factory


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusSerialClient_


class LocalConsumptionCounter(AbstractCounter):
    def __init__(self, component_config: LocalConsumptionCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__serial_client: modbus.ModbusSerialClient_ = self.kwargs['client']
        factory = consumption_counter_factory(self.component_config.configuration.type)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        if self.component_config.configuration.type == "sdm630":
            self.__client = factory(self.component_config.configuration.id, self.__serial_client,
                                    self.fault_state, silent_interval=0.06)
        else:
            self.__client = factory(self.component_config.configuration.id, self.__serial_client, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_component_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        with self.__serial_client:
            counter_state = self.__client.get_counter_state()
            if self.component_config.configuration.type == "b23":
                counter_state.exported = self.__client.get_exported()
            else:
                counter_state.exported = 0

        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=LocalConsumptionCounterSetup)
