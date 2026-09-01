from enum import Enum
from typing import Dict, Union
from modules.common.io_setup import IoDeviceSetup


class AnalogInputMapping(Enum):
    MAX_POWER = "max_power"
    MAX_CURRENT = "max_current"
    TIMESTAMP = "timestamp"


class LoadManagerConfiguration:
    def __init__(self) -> None:
        pass


def init_input():
    return {"analog": {pin.name: None for pin in AnalogInputMapping}}


def init_output():
    return {"analog": {}}


class LoadManager(IoDeviceSetup[LoadManagerConfiguration]):
    def __init__(self,
                 name: str = "openWB Lastmanager",
                 type: str = "load_manager",
                 id: Union[int, str] = 0,
                 configuration: LoadManagerConfiguration = None,
                 input: Dict[str, Dict[int, float]] = None,
                 output: Dict[str, Dict[int, float]] = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or LoadManagerConfiguration()
        if input is None:
            input = init_input()
        if output is None:
            output = init_output()
        super().__init__(name, type, id, configuration or LoadManagerConfiguration(), input=input, output=output)
