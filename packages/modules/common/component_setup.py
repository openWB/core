from typing import Generic, TypeVar

T = TypeVar("T")


class ComponentSetup(Generic[T]):
    def __init__(self, name: str, color: str, type: str, id: int, configuration: T) -> None:
        self.name = name
        self.color = color
        self.info = {"manufacturer": None, "model": None}
        self.type = type
        self.id = id
        self.configuration = configuration
