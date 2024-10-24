#!/usr/bin/env python3
import logging
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.powerdog.powerdog.config import PowerdogCounterSetup

log = logging.getLogger(__name__)


class PowerdogCounter(AbstractCounter):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, PowerdogCounterSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 modbus_id: int) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(PowerdogCounterSetup, component_config)
        self.__tcp_client = tcp_client
        self.__modbus_id = modbus_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, inverter_power: float):
        with self.__tcp_client:
            if self.component_config.configuration.position_evu:
                export_power = self.__tcp_client.read_input_registers(
                    40000, ModbusDataType.INT_32, unit=self.__modbus_id) * -1
                import_power = self.__tcp_client.read_input_registers(
                    40024, ModbusDataType.INT_32, unit=self.__modbus_id)
                power = export_power + import_power
            else:
                home_consumption = self.__tcp_client.read_input_registers(
                    40026, ModbusDataType.INT_32, unit=self.__modbus_id)
                power = home_consumption + inverter_power
                log.debug("Powerdog Hausverbrauch[W]: " + str(home_consumption))

        imported, exported = self.sim_counter.sim_count(power)
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=PowerdogCounterSetup)
