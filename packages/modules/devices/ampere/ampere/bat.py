#!/usr/bin/env python3

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.ampere.ampere.config import AmpereBatSetup


class AmpereBat(AbstractBat):
    def __init__(self,
                 component_config: AmpereBatSetup,
                 **kwargs) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    def initialiser(self):
        device_id = self.kwargs.get('device_id')
        self.modbus_id = self.kwargs.get('modbus_id')
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.client = self.kwargs.get('client')

    def update(self) -> None:
        power = self.client.read_input_registers(535, ModbusDataType.INT_16, unit=self.modbus_id)
        soc = self.client.read_input_registers(1339, ModbusDataType.UINT_16, unit=self.modbus_id)

        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=AmpereBatSetup)
