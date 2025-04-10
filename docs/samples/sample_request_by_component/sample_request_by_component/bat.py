#!/usr/bin/env python3
from typing import Optional, TypedDict, Any
from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sample_request_by_component.sample_request_by_component.config import SampleBatSetup, SampleConfiguration


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class SampleBat(AbstractBat):
    def __init__(self, component_config: SampleBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        resp = req.get_http_session().get(self.ip_address)
        power = resp.json().get("power")
        soc = resp.json().get("soc")
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
