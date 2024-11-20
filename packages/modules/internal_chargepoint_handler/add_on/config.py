from typing import Dict, Union
from modules.common.io_setup import IoDeviceSetup


class AddOnConfiguration:
    def __init__(self):
        pass


def init_input():
    return {"analog": {},
            "digital": {"21": None,
                        "24": None,
                        "31": None,
                        "32": None,
                        "33": None,
                        "36": None,
                        "40": None}
            }


def init_output():
    return {"analog": {},
            "digital": {"7": False,
                        "16": False,
                        "18": False}
            }


class AddOn(IoDeviceSetup[AddOnConfiguration]):
    def __init__(self,
                 name: str = "GPIOs auf der AddOn-Platine",
                 type: str = "add_on",
                 id: Union[int, str] = 0,
                 configuration: AddOnConfiguration = None,
                 input: Dict[str, Dict[int, float]] = None,
                 output: Dict[str, Dict[int, float]] = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or AddOnConfiguration()
        if input is None:
            input = init_input()
        if output is None:
            output = init_output()
        super().__init__(name, type, id, configuration or AddOnConfiguration(), input=input, output=output)
