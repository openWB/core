from enum import Enum
from typing import Dict
from helpermodules.auto_str import auto_str
from modules.common.io_setup import IoDeviceSetup


class AnalogInputMapping(Enum):
    LPC_END_TIME = "lpc_end_time"
    LPC_VALUE = "lpc_value"
    LPC_MSG_COUNTER = "lpc_msg_counter"
    LPP_END_TIME = "lpp_end_time"
    LPP_VALUE = "lpp_value"
    LPP_MSG_COUNTER = "lpp_msg_counter"


class DigitalInputMapping(Enum):
    LPC_ACTIVE = "lpc_active"
    LPP_ACTIVE = "lpp_active"


class CertInfo:
    def __init__(self,
                 client_ski: str = "",
                 not_before: str = "",
                 not_after: str = "",
                 issuer: str = "",
                 subject: str = ""):
        self.client_ski = client_ski
        self.not_before = not_before
        self.not_after = not_after
        self.issuer = issuer
        self.subject = subject


class EebusConfiguration:
    def __init__(self, cert_info: CertInfo = None, remote_ski: str = "", port: int = 4712) -> None:
        self.cert_info = cert_info or CertInfo()
        self.remote_ski = remote_ski
        self.port = port


def init_input():
    return {"analog": {pin.name: None for pin in AnalogInputMapping},
            "digital": {pin.name: False for pin in DigitalInputMapping}}


@auto_str
class Eebus(IoDeviceSetup[EebusConfiguration]):
    def __init__(self,
                 name: str = "Steuerbox mit EEBus-Schnittstelle",
                 type: str = "eebus",
                 id: int = 0,
                 configuration: EebusConfiguration = None,
                 input: Dict[str, Dict[int, float]] = None,
                 output: Dict[str, Dict[int, float]] = None) -> None:
        if input is None:
            input = init_input()
        super().__init__(name, type, id, configuration or EebusConfiguration(), input=input, output=output)
