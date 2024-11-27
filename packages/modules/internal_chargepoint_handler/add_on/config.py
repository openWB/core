from typing import Dict, Union
from modules.common.io_setup import IoDeviceSetup


class AddOnConfiguration:
    def __init__(self):
        pass

# 21: RSE 2
# 24: RSE 1
# 31: Taster 3 PV
# 32: Taster 1 Sofortladen
# 33: Taster 4 Stop
# 36: Taster 2 Min+PV
# 40: Taster 5 Standby


# PUD_OFF: Final = 20
# PUD_UP: Final = 22
# PUD_DOWN: Final = 21
def init_input():
    return {"analog": {},
            "digital": {"21": 20,
                        "24": 20,
                        "31": 20,
                        "32": 20,
                        "33": 20,
                        "36": 20,
                        "40": 20}
            }

# 7: LED 3
# 16: LED 2
# 18: LED 1
def init_output():
    return {"analog": {},
            "digital": {"7": None,
                        "16": None,
                        "18": None}
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
