from typing import Generic, TypeVar

T = TypeVar("T")


class ComponentSetup(Generic[T]):
    def __init__(self, name: str, type: str, id: int, configuration: T) -> None:
        self.name = name
        self.info = {"manufacturer": None, "model": None}
        self.type = type
        self.id = id
        self.configuration = configuration
        if "counter" in type.lower():
            self.color = "#dc3545"
        elif "bat" in type.lower():
            self.color = "#ffc107"
        elif "inverter" in type.lower():
            self.color = "#28a745"
        else:
            # Default color for other types
            self.color = "#000000"
