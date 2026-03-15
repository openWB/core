from typing import Dict, List


def empty_dict_factory() -> Dict:
    return {}


def empty_list_factory() -> List:
    return []


def currents_list_factory() -> List[float]:
    return [0.0]*3


def voltages_list_factory() -> List[float]:
    return [230.0]*3


def empty_io_pattern_boolean_factory():
    return [
        {
            "value": True,  # dimmen
            "matrix": {}
        },
        {
            "value": False,  # unbeschränkt
            "matrix": {}
        }
    ]


def empty_io_pattern_stepwise_factory():
    return [
        {
            "value": 1.0,  # keine Begrenzung
            "matrix": {}
        },
        {
            "value": 0.6,  # Stufe 1: 60%
            "matrix": {}
        },
        {
            "value": 0.3,  # Stufe 2: 30%
            "matrix": {}
        },
        {
            "value": 0.0,  # Stufe 3: 0%
            "matrix": {}
        }
    ]
