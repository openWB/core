from enum import Enum
import logging
from typing import Any, Dict, List, Union, cast


log = logging.getLogger(__name__)


AsDictValue = Union[None, bool, int, float, str, List["AsDictValue"], Dict[Any, "AsDictValue"]]


def asdict(value: Any) -> AsDictValue:
    """Converts an object to a dict

    This function is a simple replacement for the `dataclasses.asdict` function introduced in Python 3.7. This function
    is introduced, because openWB still requires compatibility with Python 3.5
    This function should be replaced when switching to actual Python 3.7 dataclasses.
    """
    if isinstance(value, (str, int, float)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        sequence = cast(List[Any], value)
        return [None if item is None else asdict(item) for item in sequence]
    if not isinstance(value, dict):
        value = vars(cast(object, value))
    mapping = cast(Dict[Any, Any], value)
    return {key: None if item is None else asdict(item) for key, item in mapping.items()}
