#!/usr/bin/env python3
from typing import Dict, Union
from operator import add

from dataclass_utils import dataclass_from_dict
from control import data
from modules.common import simcount
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.common.component_type import ComponentType
from modules.virtual.config import VirtualCounterSetup


class VirtualCounter:
    # Gedrehter Anschluss der Ladepunkte:
    # Phase 1 LP -> LP 0 = EVU 0, LP 1 = EVU 1, LP 2 = EVU 2
    # Phase 1 LP -> LP 0 = EVU 2, LP 1 = EVU 0, LP 2 = EVU 1
    # Phase 3 LP -> LP 0 = EVU 1, LP 1 = EVU 2, LP 2 = EVU 0
    cp_tp_evu_phase_mapping = {"1": [0, 1, 2], "2": [2, 0, 1], "3": [1, 2, 0]}

    def __init__(self, device_id: int, component_config: Union[Dict, VirtualCounterSetup]) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(VirtualCounterSetup, component_config)
        self.__sim_count = simcount.SimCountFactory().get_sim_counter()()
        self.simulation = {}
        self.__store = get_counter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self):
        self.currents = [0.0]*3
        self.incomplete_currents = False
        self.power = 0

        def add_current_power(element):
            if element.data["get"]["currents"]:
                self.currents = list(map(add, self.currents, element.data["get"]["currents"]))
            else:
                self.currents = [0, 0, 0]
                self.incomplete_currents = True
            self.power += element.data["get"]["power"]

        counter_all = data.data.counter_data["all"]
        elements = counter_all.get_all_elements_without_children(self.component_config.id)
        for element in elements:
            if element["type"] == ComponentType.CHARGEPOINT.value:
                chargepoint = data.data.cp_data[f"cp{element['id']}"]
                try:
                    evu_phases = self.cp_tp_evu_phase_mapping[str(chargepoint.data.config.phase_1)]
                except KeyError:
                    raise FaultState.error(f"Für den virtuellen Zähler muss der Anschluss der Phasen von Ladepunkt "
                                           f"{chargepoint.num} an die Phasen der EVU angegeben werden.")
                self.currents = [self.currents[i] + chargepoint.data.get.currents[evu_phases[i]] for i in range(0, 3)]

                self.power = self.power + chargepoint.data.get.power
            elif element["type"] == ComponentType.BAT.value:
                add_current_power(data.data.bat_data[f"bat{element['id']}"])
            elif element["type"] == ComponentType.COUNTER.value:
                add_current_power(data.data.counter_data[f"counter{element['id']}"])
            elif element["type"] == ComponentType.INVERTER.value:
                add_current_power(data.data.pv_data[f"pv{element['id']}"])

        self.power += self.component_config.configuration.external_consumption
        self.currents = [c + self.component_config.configuration.external_consumption/3 for c in self.currents]
        topic_str = "openWB/set/system/device/{}/component/{}/".format(self.__device_id, self.component_config.id)
        imported, exported = self.__sim_count.sim_count(
            self.power,
            topic=topic_str,
            data=self.simulation,
            prefix="bezug"
        )
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=self.power
        )
        if self.incomplete_currents is False:
            counter_state.currents = self.currents
        self.__store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=VirtualCounterSetup)
