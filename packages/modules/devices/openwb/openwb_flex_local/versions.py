from typing import Type, Union

from modules.common import b23
from modules.common import sdm


def consumption_counter_factory(type: str) -> Type[Union[sdm.Sdm120, sdm.Sdm630_72, b23.B23]]:
    if type == "sdm120":
        return sdm.Sdm120
    elif type == "sdm630":
        return sdm.Sdm630_72
    elif type == "b23":
        return b23.B23
    else:
        raise ValueError(f"Version {type} unbekannt.")
