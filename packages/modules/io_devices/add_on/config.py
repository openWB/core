from enum import Enum
from typing import Dict, Optional, Union
from modules.common.io_setup import IoDeviceSetup


class DigitalInputPinMapping(Enum):
    RSE1 = 24  # Raspberry Pi GPIO 8
    RSE2 = 21  # Raspberry Pi GPIO 9
    nurPV = 31  # Raspberry Pi GPIO 6
    SofortLa = 32  # Raspberry Pi GPIO 12
    Stop = 33  # Raspberry Pi GPIO 13
    MinPV = 36  # Raspberry Pi GPIO 16
    Standby = 40  # Raspberry Pi GPIO 21


class DigitalOutputPinMapping(Enum):
    LED1 = 18  # Raspberry Pi GPIO 24
    LED2 = 16  # Raspberry Pi GPIO 23
    LED3 = 7  # Raspberry Pi GPIO 4


class AddOnConfiguration:
    def __init__(self, host: Optional[str] = None) -> None:
        self.host = host


def init_input():
    return {"analog": {},
            "digital": {pin.name: False for pin in DigitalInputPinMapping}}


def init_output():
    return {"analog": {},
            "digital": {pin.name: False for pin in DigitalOutputPinMapping}}


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
