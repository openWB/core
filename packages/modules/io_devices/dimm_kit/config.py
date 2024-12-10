from enum import Enum
from typing import Dict, Optional

from helpermodules.auto_str import auto_str
from modules.common.io_setup import IoDeviceSetup


class AnalogInputMapping(Enum):
    AI1 = 0x00
    AI2 = 0x01
    AI3 = 0x02
    AI4 = 0x03
    AI5 = 0x04
    AI6 = 0x05
    AI7 = 0x06
    AI8 = 0x07


class DigitalInputMapping(Enum):
    DI1 = 0x00
    DI2 = 0x01
    DI3 = 0x02
    DI4 = 0x03
    DI5 = 0x04
    DI6 = 0x05
    DI7 = 0x06
    DI8 = 0x07


class DigitalOutputMapping(Enum):
    DO1 = 0x10
    DO2 = 0x11
    DO3 = 0x12
    DO4 = 0x13
    DO5 = 0x14
    DO6 = 0x15
    DO7 = 0x16
    DO8 = 0x17


class IoLanConfiguration:
    def __init__(self, host: Optional[str] = None, port: int = 8899, modbus_id: int = 1):
        self.host = host
        self.port = port
        self.modbus_id = modbus_id


def init_input():
    return {"analog": {pin.name: None for pin in AnalogInputMapping},
            "digital": {pin.name: False for pin in DigitalInputMapping}}


def init_output():
    return {"analog": {},
            "digital": {pin.name: False for pin in DigitalOutputMapping}}


@auto_str
class IoLan(IoDeviceSetup[IoLanConfiguration]):
    def __init__(self,
                 name: str = "openWB Dimm- & Control-Kit",
                 type: str = "dimm_kit",
                 id: int = 0,
                 configuration: IoLanConfiguration = None,
                 input: Dict[str, Dict[int, float]] = None,
                 output: Dict[str, Dict[int, float]] = None) -> None:
        if input is None:
            input = init_input()
        if output is None:
            output = init_output()
        super().__init__(name, type, id, configuration or IoLanConfiguration(), input=input, output=output)
