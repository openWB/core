#!/usr/bin/env python3
import logging
from typing import Any, Dict, Optional, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.simcount import SimCounter
from modules.devices.enphase.enphase.config import EnphaseBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int


class EnphaseBat(AbstractBat):
    def __init__(self, component_config: EnphaseBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")

    def update(self, response, live_data: Optional[Dict[str, Any]] = None) -> None:
        if live_data is None:
            raise ValueError("Es stehen keine Daten vom Speicher zur Verfügung.")
        bat_data = live_data["meters"]["storage"]
        if bat_data is None:
            # configuration wrong or error
            raise ValueError("Es konnten keine Daten vom Speicher gelesen werden.")
        soc = live_data["meters"]["soc"]
        power = bat_data['agg_p_mw'] / -1000  # negative is charging
        # powers = [bat_data['agg_p_ph_a_mw'] / 1000,
        #           bat_data['agg_p_ph_b_mw'] / 1000,
        #           bat_data['agg_p_ph_c_mw'] / 1000]
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            imported=imported,
            exported=exported,
            soc=soc,
            power=power,
            # powers=powers
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=EnphaseBatSetup)
