import logging


from control import data
from helpermodules import pub
from helpermodules.utils.topic_parser import get_second_index
from modules.common.component_type import ComponentType, type_to_topic_mapping
from modules.common.simcount.simcounter_state import SimCounterState

POSTFIX_EXPORT = "watt0neg"
POSTFIX_IMPORT = "watt0pos"

log = logging.getLogger(__name__)


class SimCounterStoreBroker:
    def initialize(self, component_type: ComponentType, topic: str, power: float, timestamp: float) -> SimCounterState:
        state = SimCounterState(
            timestamp, power,
            imported=restore_last_energy(
                topic, "imported", component_type) if component_type != ComponentType.INVERTER else 0,
            exported=restore_last_energy(topic, "exported", component_type))
        self.save(topic, state)
        return state

    def save(self, topic: str, state: SimCounterState):
        pub.Pub().pub(topic + "simulation", vars(state))


def restore_last_energy(topic: str, value: str, component_type: ComponentType):
    try:
        module_type = type_to_topic_mapping(component_type)
        module = getattr(data.data, f"{module_type}_data")[f"{module_type}{get_second_index(topic)}"].data.get
        return getattr(module, value)
    except AttributeError:
        if (value == "imported" and component_type == ComponentType.INVERTER):
            return 0
    except ValueError:
        # Wenn kein Index enthalten, ist es Hausverbrauch.
        if value == "exported":
            # wird beim Hausverbrauch nicht ausgewertet.
            return 0
        elif value == "imported":
            return data.data.counter_all_data.data.set.imported_home_consumption
