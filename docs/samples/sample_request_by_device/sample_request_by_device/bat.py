#!/usr/bin/env python3
from typing import Optional, TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.sample_request_by_device.sample_request_by_device.config import SampleBatSetup


class KwargsDict(TypedDict):
    device_id: int


class SampleBat(AbstractBat):
    def __init__(self, component_config: SampleBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        # hier die Werte aus der response parsen
        power = response.get("power")
        soc = response.get("soc")
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        # Wenn der Speicher die Steuerung der Ladeleistung unterstützt, muss bei Übergabe einer Zahl auf aktive
        # Speichersteurung umgeschaltet werden, sodass der Speicher mit der übergebenen Leistung lädt/entlädt. Wird
        # None übergeben, muss der Speicher die Null-Punkt-Ausregelung selbst übernehmen.
        self.client.write_registers(reg, power_limit)
        # Wenn der Speicher keine Steuerung der Ladeleistung unterstützt
        pass

    def power_limit_controllable(self) -> bool:
        # Wenn der Speicher die Steuerung der Ladeleistung unterstützt, muss True zurückgegeben werden.
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SampleBatSetup)
