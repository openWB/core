from typing import Dict
from modules.common.io_setup import IoDeviceSetup


class AddOnConfiguration:
    def __init__(self):
        pass


def digital_input_init():
    return {"21": False,
            "24": False,
            "31": False,
            "32": False,
            "33": False,
            "36": False,
            "40": False}


def digital_output_init():
    return {"7": False,
            "16": False,
            "18": False}


class AddOn(IoDeviceSetup[AddOnConfiguration]):
    def __init__(self,
                 name: str = "GPIOs auf der AddOn-Platine",
                 type: str = "add_on",
                 id: int = 0,
                 configuration: AddOnConfiguration = None,
                 digital_input: Dict[int, bool] = None,
                 digital_output: Dict[int, bool] = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or AddOnConfiguration()
        if digital_input is None:
            digital_input = digital_input_init()
        if digital_output is None:
            digital_output = digital_output_init()
        super().__init__(name, type, id, configuration or AddOnConfiguration(),
                         digital_input=digital_input, digital_output=digital_output)
