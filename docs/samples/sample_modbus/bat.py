#!/usr/bin/env python3
from typing import Optional
from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sample_modbus.config import SampleBatSetup


class SampleBat(AbstractBat):
    def __init__(self, device_id: int, component_config: SampleBatSetup, client: ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SampleBatSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.client = client

    def update(self) -> None:
        power = self.client.read_holding_registers(reg, ModbusDataType.INT_32, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        # Methode entfernen, falls der Speicher keine Steuerung der Ladeleistung unterstützt
        # Wenn der Speicher die Steuerung der Ladeleistung unterstützt, muss bei Übergabe einer Zahl auf aktive
        # Speichersteurung umgeschaltet werden, sodass der Speicher mit der übergebenen Leistung lädt/entlädt. Wird
        # None übergeben, muss der Speicher die Null-Punkt-Ausregelung selbst übernehmen.
        self.client.write_registers(reg, power_limit)


component_descriptor = ComponentDescriptor(configuration_factory=SampleBatSetup)
