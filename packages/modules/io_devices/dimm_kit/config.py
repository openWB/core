from typing import Dict, Optional

from helpermodules.auto_str import auto_str
from modules.common.io_setup import IoDeviceSetup


class IoLanConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 8899, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


def init_input():
    return {"analog": {str(i): None for i in range(1, 9)},
            "digital": {str(i): None for i in range(1, 9)}}


def init_output():
    return {"analog": {},
            "digital": {str(i): False for i in range(16, 24)}}


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
