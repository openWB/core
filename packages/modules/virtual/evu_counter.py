#!/usr/bin/env python3
from control import data
from helpermodules.log import MainLogger
from modules.common import simcount
from modules.common.component_state import CounterState
from modules.common.fault_state import ComponentInfo
from modules.common.store import get_counter_value_store


def get_default_config() -> dict:
    return {
        "name": "Virtueller EVU-Zähler",
        "type": "evu_counter",
        "id": None,
        "configuration": {
            "home_consumption": 400
        }
    }


class VirtualEvuCounter:
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
        try:
            pv = data.data.pv_data["all"].data["get"]["power"]
            bat = data.data.bat_data["all"].data["get"]["power"]
            cp = data.data.cp_data["all"].data["get"]["power_all"]
            power_all = pv + bat + cp + self.component_config["configuration"]["home_consumption"]

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
                imported=imported,
                exported=exported,
                power_all=power_all
            )
            MainLogger().debug("Virtual Leistung[W]: " + str(counter_state.power_all))
            self.__store.set(counter_state)
        except Exception as e:
            MainLogger().exception(str(e))
