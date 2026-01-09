from typing import Generic, List, TypeVar

from control.consumer.usage import ConsumerUsage


T = TypeVar("T")


class ConsumerSetup(Generic[T]):
    def __init__(self, name: str, type: str, id: int, vendor: str, configuration: T, usage: List[ConsumerUsage]) -> None:
        self.name = name
        self.info = {"manufacturer": None, "model": None}
        self.type = type
        self.id = id
        self.configuration = configuration
        self.vendor = vendor
        self.usage = usage
