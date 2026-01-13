from typing import Optional
from modules.common.component_type import ComponentType
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._battery import get_bat_value_store
from modules.common.store._consumer import get_consumer_value_store
from modules.common.store._counter import get_counter_value_store
from modules.common.store._inverter import get_inverter_value_store


def get_component_value_store(component_type: str,
                              component_num: int,
                              add_child_values: bool = False,
                              simcounter: Optional[SimCounter] = None):
    if component_type == ComponentType.BAT.value:
        return get_bat_value_store(component_num, add_child_values)
    elif component_type == ComponentType.CONSUMER.value:
        return get_consumer_value_store(component_num, add_child_values)
    elif component_type == ComponentType.COUNTER.value:
        return get_counter_value_store(component_num, add_child_values, simcounter)
    elif component_type == ComponentType.INVERTER.value:
        return get_inverter_value_store(component_num, add_child_values)
