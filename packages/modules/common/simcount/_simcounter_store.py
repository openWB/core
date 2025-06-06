import logging
from abc import abstractmethod
from typing import Optional


from control import data
from helpermodules import pub
from helpermodules.utils.topic_parser import get_index, get_second_index
from modules.common.component_type import type_to_topic_mapping
from modules.common.simcount.simcounter_state import SimCounterState

POSTFIX_EXPORT = "watt0neg"
POSTFIX_IMPORT = "watt0pos"

log = logging.getLogger(__name__)


class SimCounterStore:
    @abstractmethod
    def load(self, prefix: str, topic: str) -> Optional[SimCounterState]:
        pass

    @abstractmethod
    def save(self, prefix: str, topic: str, state: SimCounterState):
        pass

    @abstractmethod
    def initialize(self, prefix: str, topic: str, power: float, timestamp: float) -> SimCounterState:
        pass


class SimCounterStoreBroker(SimCounterStore):
    def initialize(self, prefix: str, topic: str, power: float, timestamp: float) -> SimCounterState:
        state = SimCounterState(timestamp, power, imported=restore_last_energy(
            topic, "imported") if "pv" not in prefix else 0, exported=restore_last_energy(topic, "exported"))
        self.save(prefix, topic, state)
        return state

    def load(self, prefix: str, topic: str) -> Optional[SimCounterState]:
        return None

    def save(self, prefix: str, topic: str, state: SimCounterState):
        pub.Pub().pub(topic + "simulation", vars(state))


def restore_last_energy(topic: str, value: str):
    try:
        device_id = get_index(topic)
        component_id = get_second_index(topic)
        module_type = type_to_topic_mapping(
            data.data.system_data[f"device{device_id}"].components[f"component{component_id}"].component_config.type)
        module = getattr(data.data, f"{module_type}_data")[f"{module_type}{get_second_index(topic)}"].data.get
        return getattr(module, value)
    except AttributeError:
        if (value == "imported" and
                "inverter" in data.data.system_data[f"device{device_id}"].components[
                    f"component{component_id}"].component_config.type):
            return 0
    except ValueError:
        # Wenn kein Index enthalten, ist es Hausverbrauch.
        if value == "exported":
            # wird beim Hausverbrauch nicht ausgewertet.
            return 0
        elif value == "imported":
            return data.data.counter_all_data.data.set.imported_home_consumption


def get_sim_counter_store() -> SimCounterStore:
    return SimCounterStoreBroker()
