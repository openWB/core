from typing import Generic, Optional, TypeVar, Tuple

from control.consumer.usage import ConsumerUsage
from helpermodules.constants import DEFAULT_COLORS


T = TypeVar("T")


class ConsumerSetup(Generic[T]):
    def __init__(self,
                 name: str,
                 type: str,
                 id: int,
                 vendor: str,
                 configuration: T,
                 usage: Tuple[ConsumerUsage, ...],
                 color: Optional[str] = None) -> None:
        self.name = name
        self.info = {"manufacturer": None, "model": None}
        self.type = type
        self.id = id
        self.configuration = configuration
        self.vendor = vendor
        self.usage = usage
        if color:
            self.color = color
        else:
            self.color = DEFAULT_COLORS.CONSUMER.value
