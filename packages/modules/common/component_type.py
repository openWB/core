from enum import Enum
from typing import Type


class ComponentType(Enum):
    BACKUP_CLOUD = "backup_cloud"
    BAT = "bat"
    BAT_PRICE = "bat_price"
    CHARGEPOINT = "cp"
    CONSUMER = "consumer"
    COUNTER = "counter"
    FEED_IN_PRICE = "feed_in_price"
    TARIFF = "electricity_tariff"
    GRID_FEE = "grid_tariff"
    WALLBOX_SOCKET = "wallbox_socket"
    INVERTER = "inverter"
    IO = "io"
    PV_PRICE = "pv_price"
    VEHICLE = "vehicle"


def special_to_general_type_mapping(component_type: str) -> ComponentType:
    if "bat" in component_type:
        return ComponentType.BAT
    elif "consumer" in component_type:
        return ComponentType.CONSUMER
    elif "counter" in component_type:
        return ComponentType.COUNTER
    elif "inverter" in component_type:
        return ComponentType.INVERTER
    elif "cp" in component_type:
        return ComponentType.CHARGEPOINT
    else:
        raise TypeError("Typ "+component_type+" konnte keinem bekannten Komponenten-Typ zugeordnet werden.")


def type_to_topic_mapping(component_type: str) -> str:
    # vor "bat", da "bat_price" den Teilstring "bat" enthält
    if ComponentType.FEED_IN_PRICE.value in component_type:
        return "optional/ep/feed_in_price"
    elif ComponentType.BAT_PRICE.value in component_type:
        return "optional/ep/bat_price"
    elif ComponentType.PV_PRICE.value in component_type:
        return "optional/ep/pv_price"
    elif "bat" in component_type:
        return "bat"
    elif "consumer" in component_type:
        return "consumer"
    elif "counter" in component_type:
        return "counter"
    elif "wallbox_socket" in component_type:
        return "internal_socket"
    elif "inverter" in component_type:
        return "pv"
    elif ComponentType.TARIFF.value in component_type:
        return "optional/ep/flexible_tariff"
    elif ComponentType.GRID_FEE.value in component_type:
        return "optional/ep/grid_fee"
    elif ComponentType.IO.value in component_type:
        return "io/states"
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
    if component_type == ComponentType.BACKUP_CLOUD:
        return "Backup Cloud"
    elif component_type == ComponentType.BAT:
        return "Speicher"
    elif component_type == ComponentType.CHARGEPOINT:
        return "Ladepunkt"
    elif component_type == ComponentType.CONSUMER:
        return "Verbraucher"
    elif component_type == ComponentType.COUNTER:
        return "Zähler"
    elif component_type == ComponentType.TARIFF:
        return "Stromtarif"
    elif component_type == ComponentType.GRID_FEE:
        return "Netzentgelt"
    elif component_type == ComponentType.INVERTER:
        return "Wechselrichter"
    elif component_type == ComponentType.IO:
        return "IO-Geräte"
    elif component_type == ComponentType.FEED_IN_PRICE:
        return "Einspeisevergütung"
    elif component_type == ComponentType.PV_PRICE:
        return "Preis für Erzeugung"
    elif component_type == ComponentType.BAT_PRICE:
        return "Preis für Speicherentladung"
    elif component_type == ComponentType.VEHICLE:
        return "Fahrzeug"
    else:
        return "Unbekannter Komponenten-Typ"


class ComponentDescriptor:
    def __init__(self, configuration_factory: Type):
        self.configuration_factory = configuration_factory
