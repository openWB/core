#!/usr/bin/env python3
from typing import Dict, TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.fronius.fronius.config import FroniusSecondaryInverterSetup


class KwargsDict(TypedDict):
    device_id: int


class FroniusSecondaryInverter(AbstractInverter):
    def __init__(self, component_config: FroniusSecondaryInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict) -> None:
        # Rückgabewert ist die aktuelle Wirkleistung in [W].
        if isinstance(response, Exception):
            power = 0.0
        else:
            try:
                secondary_data = response["Body"]["Data"]["SecondaryMeters"][str(
                    self.component_config.configuration.id)]
                if secondary_data["Category"] == "METER_CAT_WR":
                    power = float(secondary_data["P"]) * -1
                else:
                    raise ValueError(f"Sekundäres Gerät {self.component_config.configuration.id} "
                                     "ist kein Wechselrichter.")
            except TypeError:
                # Ohne PV Produktion liefert der WR 'null', ersetze durch Zahl 0
                power = 0

        _, exported = self.sim_counter.sim_count(power)

        self.store.set(InverterState(
            power=power,
            exported=exported
        ))


component_descriptor = ComponentDescriptor(configuration_factory=FroniusSecondaryInverterSetup)
