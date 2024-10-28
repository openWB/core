
from typing import Dict, Generic, Optional, TypeVar

from dataclass_utils.factories import empty_dict_factory


T = TypeVar("T")


class IoDeviceSetup(Generic[T]):
    def __init__(self,
                 name: str,
                 type: str,
                 id: int,
                 configuration: T,
                 analog_input: Optional[Dict[int, float]] = None,
                 analog_output: Optional[Dict[int, float]] = None,
                 digital_input: Optional[Dict[int, float]] = None,
                 digital_output: Optional[Dict[int, float]] = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration
        self.analog_input = analog_input if analog_input is not None else empty_dict_factory()
        self.analog_output = analog_output if analog_output is not None else empty_dict_factory()
        self.digital_input = digital_input if digital_input is not None else empty_dict_factory()
        self.digital_output = digital_output if digital_output is not None else empty_dict_factory()
