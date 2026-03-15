
from typing import Dict, Generic, Optional, TypeVar

from dataclass_utils.factories import empty_dict_factory


T = TypeVar("T")


class IoDeviceSetup(Generic[T]):
    def __init__(self,
                 name: str,
                 type: str,
                 id: int,
                 configuration: T,
                 input: Optional[Dict[str, Dict[int, float]]] = None,
                 output: Optional[Dict[str, Dict[int, float]]] = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration
        self.input = input if input is not None else empty_dict_factory()
        self.output = output if output is not None else empty_dict_factory()
