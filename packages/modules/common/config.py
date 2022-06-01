from typing import Callable, Dict


class Config:
    def __init__(self, child_locals) -> None:
        for key, value in child_locals.items():
            if key != "self":
                setattr(self, key, value)


def from_dict(device_config: Dict, class_type: Callable) -> Callable:
    try:
        values = []
        keys = class_type().__dict__.keys()
        for key in keys:
            if isinstance(device_config[key], Dict):
                values.append(from_dict(device_config[key], class_type.config_class))
            else:
                values.append(device_config[key])
    except KeyError as e:
        raise Exception(
            "Illegal configuration <{}>: Expected object with properties: {}".format(device_config, keys)
        ) from e
    return class_type(*values)


def to_dict(class_type: Callable) -> Dict:
    dictionary = {}
    attributes = class_type.__dict__
    for key, value in attributes.items():
        if class_type.config_class:
            if isinstance(value, class_type.config_class):
                dictionary.update({key: to_dict(value)})
            else:
                dictionary.update({key: value})
        else:
            dictionary.update({key: value})
    return dictionary
