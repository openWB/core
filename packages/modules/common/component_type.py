from enum import Enum

def special_to_general_type_mapping(component_type: str) -> str:
    if "bat" in component_type:
        return "bat"
    elif "counter" in component_type:
        return "counter"
    elif "inverter" in component_type:
        return "pv"
    else:
        return component_type

class ComponentType(Enum):
    BAT = "bat"
    CHARGEPOINT = "cp"
    COUNTER = "counter"
    INVERTER = "inverter"
