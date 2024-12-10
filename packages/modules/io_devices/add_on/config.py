from enum import Enum
from typing import Dict, Optional, Union
from modules.common.io_setup import IoDeviceSetup


class DigitalInputMapping(Enum):
    RSE1 = 24
    RSE2 = 21
    nurPV = 31
    SofortLa = 32
    Stop = 33
    MinPV = 36
    Standby = 40


class DigitalOutputMapping(Enum):
    LED1 = 18
    LED2 = 16
    LED3 = 7


class AddOnConfiguration:
    def __init__(self, host: Optional[str] = None) -> None:
        self.host = host


def init_input():
    return {"analog": {},
            "digital": {pin.name: False for pin in DigitalInputMapping}}


def init_output():
    return {"analog": {},
            "digital": {pin.name: False for pin in DigitalOutputMapping}}


class AddOn(IoDeviceSetup[AddOnConfiguration]):
    def __init__(self,
                 name: str = "Kontakte der AddOn-Platine",
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
