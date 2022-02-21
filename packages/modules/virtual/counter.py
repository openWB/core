#!/usr/bin/env python3
from operator import add

from control import data
from helpermodules.log import MainLogger
from modules.common import simcount
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.common.component_type import ComponentType


def get_default_config() -> dict:
    return {
        "name": "Virtueller Zähler",
        "type": "counter",
        "id": None,
        "configuration": {
            "external_consumption": 400
        }
    }


class VirtualCounter:

    # Gedrehter Anschluss der Ladepunkte:
    # Phase 1 LP -> LP-P 0 = EVU-P 0, LP-P 1 = EVU-P 1, LP-P 2 = EVU-P 2
    # Phase 1 LP -> LP-P 0 = EVU-P 1, LP-P 1 = EVU-P 2, LP-P 2 = EVU-P 0
    # Phase 3 LP -> LP-P 0 = EVU-P 2, LP-P 1 = EVU-P 0, LP-P 2 = EVU-P 1
    cp_tp_evu_phase_mapping = {"1": [0, 1, 2], "2": [1, 2, 0], "3": [2, 0, 1]}

    def __init__(self, device_id: int, component_config: dict) -> None:
        self.__device_id = device_id
        self.component_config = component_config
        self.__sim_count = simcount.SimCountFactory().get_sim_counter()()
        self.simulation = {}
        self.__store = get_counter_value_store(component_config["id"])
        self.component_info = ComponentInfo(self.component_config["id"],
                                            self.component_config["name"],
                                            self.component_config["type"])

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
        elements = counter_all.get_entry_of_element(self.component_config["id"])["children"]
        for element in elements:
            if element["type"] == ComponentType.CHARGEPOINT.value:
                chargepoint = data.data.cp_data[f"cp{element['id']}"]
                try:
                    evu_phases = self.cp_tp_evu_phase_mapping[str(chargepoint.data["config"]["phase_1"])]
                except KeyError:
                    raise FaultState.error(f"Für den virtuellen Zähler muss der Anschluss der Phasen von Ladepunkt "
                                           f"{chargepoint.cp_num} an die Phasen der EVU angegeben werden.")
                self.currents = [self.currents[i] + chargepoint.data["get"]
                                 ["currents"][evu_phases[i]] for i in range(0, 3)]

                self.power = self.power + chargepoint.data["get"]["power"]
            elif element["type"] == ComponentType.BAT.value:
                add_current_power(data.data.bat_data[f"bat{element['id']}"])
            elif element["type"] == ComponentType.COUNTER.value:
                add_current_power(data.data.counter_data[f"counter{element['id']}"])
            elif element["type"] == ComponentType.INVERTER.value:
                add_current_power(data.data.pv_data[f"pv{element['id']}"])

        topic_str = "openWB/set/system/device/{}/component/{}/".format(self.__device_id, self.component_config["id"])
        imported, exported = self.__sim_count.sim_count(
            self.power,
            topic=topic_str,
            data=self.simulation,
            prefix="bezug"
        )
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=(self.power + self.component_config["configuration"]["external_consumption"])
        )
        if self.incomplete_currents is False:
            counter_state.currents = self.currents

        MainLogger().debug("Virtual Leistung[W]: " + str(counter_state.power))
        self.__store.set(counter_state)
