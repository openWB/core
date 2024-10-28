from typing import Dict, Optional

from helpermodules.auto_str import auto_str
from modules.common.io_setup import IoDeviceSetup


class IoLanConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 8899, modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


def analog_input_init():
    return {i: 0 for i in range(1, 9)}


def digital_input_init():
    return {i: False for i in range(1, 9)}


def digital_output_init():
    return {i: False for i in range(16, 24)}


@auto_str
class IoLan(IoDeviceSetup[IoLanConfiguration]):
    def __init__(self,
                 name: str = "openWB Dimm- & Control-Kit",
                 type: str = "dimm_kit",
                 id: int = 0,
                 configuration: IoLanConfiguration = None,
                 analog_input: Dict[int, float] = None,
                 digital_input: Dict[int, bool] = None,
                 digital_output: Dict[int, bool] = None) -> None:
        if analog_input is None:
            analog_input = analog_input_init()
        if digital_input is None:
            digital_input = digital_input_init()
        if digital_output is None:
            digital_output = digital_output_init()
        super().__init__(name, type, id, configuration or IoLanConfiguration(), analog_input=analog_input,
                         digital_input=digital_input, digital_output=digital_output)
