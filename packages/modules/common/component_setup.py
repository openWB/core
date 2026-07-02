from typing import Generic, Optional, TypeVar
import logging

from helpermodules.constants import DEFAULT_COLORS

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
        else:
            if "counter" in type.lower():
                self.color = DEFAULT_COLORS.COUNTER.value
            elif "bat" in type.lower():
                self.color = DEFAULT_COLORS.BATTERY.value
            elif "inverter" in type.lower():
                self.color = DEFAULT_COLORS.INVERTER.value
            else:
                # Default color for other types
                log.warning(f"Unknown component type '{type}' for component '{name}'. Using default color.")
                self.color = DEFAULT_COLORS.UNKNOWN.value
