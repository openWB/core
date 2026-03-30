from typing import Generic, Optional, TypeVar
import logging

T = TypeVar("T")

log = logging.getLogger(__name__)


class ComponentSetup(Generic[T]):
    def __init__(self, name: str, type: str, id: int, configuration: T, color: Optional[str] = None) -> None:
        self.name = name
        self.info = {"manufacturer": None, "model": None}
        self.type = type
        self.id = id
        self.configuration = configuration
        if color:
            self.color = color
            log.error(f"Color specified for component '{self.name}' of type '{self.type}': {color}")
        else:
            log.error(f"No color specified for component '{self.name}' of type '{self.type}'. Using default color.")
            if "counter" in type.lower():
                self.color = "#dc3545"
            elif "bat" in type.lower():
                self.color = "#ffc107"
            elif "inverter" in type.lower():
                self.color = "#28a745"
            else:
                # Default color for other types
                self.color = "#000000"
