from enum import Enum
from typing import Type


class ComponentType(Enum):
    BAT = "bat"
    CHARGEPOINT = "cp"
    COUNTER = "counter"
    ELECTRICITY_TARIFF = "electricity_tariff"
    INVERTER = "inverter"
    RIPPLE_CONTROL_RECEIVER = "ripple_control_receiver"


def special_to_general_type_mapping(component_type: str) -> ComponentType:
    if "bat" in component_type:
        return ComponentType.BAT
    elif "counter" in component_type:
        return ComponentType.COUNTER
    elif "inverter" in component_type:
        return ComponentType.INVERTER
    elif "cp" in component_type:
        return ComponentType.CHARGEPOINT
    else:
        raise TypeError("Typ "+component_type+" konnte keinem bekannten Komponenten-Typ zugeordnet werden.")


def type_to_topic_mapping(component_type: str) -> str:
    if "bat" in component_type:
        return "bat"
    elif "counter" in component_type:
        return "counter"
    elif "inverter" in component_type:
        return "pv"
    elif ComponentType.ELECTRICITY_TARIFF.value in component_type:
        return "optional/et"
    else:
        return component_type


def type_topic_mapping_comp(component_type: str) -> str:
    if "bat" in component_type:
        return "houseBattery"
    elif "counter" in component_type:
        return "evu"
    elif "inverter" in component_type:
        return "pv"
    elif "vehicle" in component_type or "chargepoint" in component_type:
        return "lp"
    else:
        raise Exception("Unbekannter Komponenten-Typ: " + component_type)


def component_type_to_readable_text(component_type: ComponentType):
    if component_type == ComponentType.BAT:
        return "Speicher"
    elif component_type == ComponentType.COUNTER:
        return "Zähler"
    elif component_type == ComponentType.CHARGEPOINT:
        return "Ladepunkt"
    elif component_type == ComponentType.INVERTER:
        return "Wechselrichter"


class ComponentDescriptor:
    def __init__(self, configuration_factory: Type):
        self.configuration_factory = configuration_factory
