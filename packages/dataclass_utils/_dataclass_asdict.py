from dataclasses import fields, is_dataclass
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
    if value is None:
        return None
    elif isinstance(value, (str, int, float)):
        return value
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(value, (list, tuple)):
        sequence = cast(List[Any], value)
        return [None if item is None else asdict(item) for item in sequence]
    elif is_dataclass(value) and not isinstance(value, type):
        # Bei Dataclasses nur deklarierte Felder serialisieren
        return {
            field.name: asdict(getattr(value, field.name))
            for field in fields(value)
        }
    elif isinstance(value, dict):
        mapping = cast(Dict[Any, Any], value)
        return {key: None if item is None else asdict(item) for key, item in mapping.items()}
    else:
        default_getstate = getattr(object, "__getstate__", None)
        state = getattr(value, "__getstate__", None)
        value_class = type(cast(object, value))
        if callable(state) and getattr(value_class, "__getstate__", None) is not default_getstate:
            return asdict(state())
        value = vars(cast(object, value))
        mapping = cast(Dict[Any, Any], value)
        return {key: None if item is None else asdict(item) for key, item in mapping.items()}
