from typing import Optional
from modules.common.component_type import ComponentType, special_to_general_type_mapping
from modules.common.simcount._simcounter import SimCounter
from modules.common.store._battery import get_bat_value_store
from modules.common.store._consumer import get_consumer_value_store
from modules.common.store._counter import get_counter_value_store
from modules.common.store._inverter import get_inverter_value_store


def get_component_value_store(component_type_str: str,
                              component_num: int,
                              add_child_values: bool = False,
                              simcounter: Optional[SimCounter] = None):
    component_type = special_to_general_type_mapping(
        component_type_str.value if isinstance(component_type_str, ComponentType) else component_type_str)
    if ComponentType.BAT == component_type:
        return get_bat_value_store(component_num)
    elif ComponentType.CONSUMER == component_type:
        return get_consumer_value_store(component_num)
    elif ComponentType.COUNTER == component_type:
        return get_counter_value_store(component_num, add_child_values, simcounter)
    elif ComponentType.INVERTER == component_type:
        return get_inverter_value_store(component_num)
    else:
        raise ValueError(f"Unknown component type: {component_type}")
