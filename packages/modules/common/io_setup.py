
from typing import Dict, Generic, Optional, TypeVar, Union

from dataclass_utils.factories import empty_dict_factory


T = TypeVar("T")


class IoDeviceSetup(Generic[T]):
    def __init__(self,
                 name: str,
                 type: str,
                 id: int,
                 configuration: T,
                 input: Optional[Dict[str, Union[Dict[str, bool], Dict[str, float], Dict[str, None]]]] = None,
                 output: Optional[Dict[str, Union[Dict[str, bool], Dict[str, float], Dict[str, None]]]] = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration
        self.input = input if input is not None else empty_dict_factory()
        self.output = output if output is not None else empty_dict_factory()
