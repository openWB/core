from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Type, TypeVar

C = TypeVar("C")


@dataclass
class AbstractConfiguration:
    pass


@dataclass
class AbstractSetup:
    name: str = ""
    type: str = ""
    id: int = 0
    configuration = Callable[[C], None]


T = TypeVar("T", AbstractConfiguration, AbstractSetup)


def from_dict(device_config: Dict, class_type: Type[T]) -> T:
    values = []
    keys = class_type().__dict__.keys()
    try:
        for key in keys:
            if isinstance(device_config[key], Dict):
                values.append(from_dict(device_config[key], type(getattr(class_type, key))))
            else:
                values.append(device_config[key])
    except KeyError as e:
        raise Exception(
            "Illegal configuration <{}>: Expected object with properties: {}".format(device_config, keys)
        ) from e
    return class_type(*values)


def to_dict(class_type: T) -> Dict:
    dictionary = {}
    attributes = class_type.__dict__
    for key, value in attributes.items():
        if not isinstance(value, (bool, str, int, float, List, Dict, Tuple, type(None))):
            dictionary.update({key: to_dict(value)})
        else:
            dictionary.update({key: value})
    return dictionary
