#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.openwb.openwb_flex.config import ConsumptionCounterFlexSetup
from modules.devices.openwb.openwb_flex.versions import consumption_counter_factory


class ConsumptionCounterFlex(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, ConsumptionCounterFlexSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(ConsumptionCounterFlexSetup, component_config)
        factory = consumption_counter_factory(
            self.component_config.configuration.type)
        self.__client = factory(self.component_config.configuration.id, tcp_client)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self):
        with self.__tcp_client:
            voltages = self.__client.get_voltages()
            powers, power = self.__client.get_power()
            frequency = self.__client.get_frequency()
            power_factors = self.__client.get_power_factors()
            imported = self.__client.get_imported()
            currents = self.__client.get_currents()
            if self.component_config.configuration.type == "b23":
                exported = self.__client.get_exported()
            else:
                exported = 0

        counter_state = CounterState(
            voltages=voltages,
            currents=currents,
            powers=powers,
            power_factors=power_factors,
            imported=imported,
            exported=exported,
            power=power,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=ConsumptionCounterFlexSetup)
