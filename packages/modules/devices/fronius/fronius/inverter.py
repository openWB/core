#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.fronius.fronius.config import FroniusInverterSetup


class FroniusInverter:
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, FroniusInverterSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(FroniusInverterSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict) -> None:
        # Rückgabewert ist die aktuelle Wirkleistung in [W].
        if isinstance(response, Exception):
            power = 0.0
        else:
            try:
                power = float(response["Body"]["Data"]["Site"]["P_PV"]) * -1
            except TypeError:
                # Ohne PV Produktion liefert der WR 'null', ersetze durch Zahl 0
                power = 0

        _, exported = self.sim_counter.sim_count(power)

        self.store.set(InverterState(
            power=power,
            exported=exported
        ))


component_descriptor = ComponentDescriptor(configuration_factory=FroniusInverterSetup)
