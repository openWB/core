#!/usr/bin/env python3
from control import data
from helpermodules.log import MainLogger
from modules.common import simcount
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store


def get_default_config() -> dict:
    return {
        "name": "Virtueller Ladepunkt-Zähler",
        "type": "cp_counter",
        "id": None,
        "configuration": {
        }
    }


class VirtualCpCounter:
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
        # "Angeschlossene" Ladepunkte ermitteln
        counter_name = "counter"+str(self.component_config["id"])
        chargepoints = data.data.counter_data["all"].get_chargepoints_of_counter(counter_name)
        # Ladeleistungen, Ströme addieren
        currents = [0.0]*3
        power_all = 0
        for cp in chargepoints:
            chargepoint = data.data.cp_data[cp]
            # Gedrehter Anschluss der Ladepunkte:
            # Phase 1 LP = Phase 1 EVU -> LP-P 0 = EVU-P 0, LP-P 1 = EVU-P 1, LP-P 2 = EVU-P 2
            # Phase 1 LP = Phase 2 EVU -> LP-P 0 = EVU-P 1, LP-P 1 = EVU-P 2, LP-P 2 = EVU-P 0
            # Phase 3 LP = Phase 3 EVU -> LP-P 0 = EVU-P 2, LP-P 1 = EVU-P 0, LP-P 2 = EVU-P 1
            if chargepoint.data["config"]["phase_1"] == 1:
                evu_phases = [0, 1, 2]
            elif chargepoint.data["config"]["phase_1"] == 2:
                evu_phases = [1, 2, 0]
            elif chargepoint.data["config"]["phase_1"] == 3:
                evu_phases = [2, 0, 1]
            else:
                raise FaultState.error("Fuer den virtuellen Zaehler muss der Anschluss der Phasen vom Ladepunkt " +
                                       str(chargepoint.cp_num) + " an die Phasen der EVU angegeben werden.")
            currents[0] = currents[0] + chargepoint.data["get"]["currents"][evu_phases[0]]
            currents[1] = currents[1] + chargepoint.data["get"]["currents"][evu_phases[1]]
            currents[2] = currents[2] + chargepoint.data["get"]["currents"][evu_phases[2]]

            power_all = power_all + chargepoint.data["get"]["power_all"]
        power_phase = [230*c for c in currents]

        topic_str = "openWB/set/system/device/{}/component/{}/".format(
            self.__device_id, self.component_config["id"]
        )
        imported, exported = self.__sim_count.sim_count(
            power_all,
            topic=topic_str,
            data=self.simulation,
            prefix="bezug"
        )
        counter_state = CounterState(
            currents=currents,
            powers=power_phase,
            imported=imported,
            exported=exported,
            power_all=power_all
        )
        MainLogger().debug("Virtual Leistung[W]: " + str(counter_state.power_all))
        self.__store.set(counter_state)
