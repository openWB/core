from typing import Dict, List


def empty_dict_factory() -> Dict:
    return {}


def emtpy_list_factory() -> List:
    return []


def currents_list_factory() -> List[float]:
    return [0.0]*3


def voltages_list_factory() -> List[float]:
    return [230.0]*3
