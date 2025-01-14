from typing import Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.sungrow.sungrow.version import Version
from modules.devices.sungrow.sungrow.firmware import Firmware
from ..vendor import vendor_descriptor


class SungrowConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1,
                 version: Version = Version.SG,
                 firmware: Firmware = Firmware.v1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.version = version
        self.firmware = firmware


class Sungrow:
    def __init__(self,
                 name: str = "Sungrow",
                 type: str = "sungrow",
                 id: int = 0,
                 configuration: SungrowConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SungrowConfiguration()


class SungrowBatConfiguration:
    def __init__(self):
        pass


class SungrowBatSetup(ComponentSetup[SungrowBatConfiguration]):
    def __init__(self,
                 name: str = "Sungrow Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SungrowBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowBatConfiguration())


class SungrowCounterConfiguration:
    def __init__(self):
        pass


class SungrowCounterSetup(ComponentSetup[SungrowCounterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SungrowCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowCounterConfiguration())


class SungrowInverterConfiguration:
    def __init__(self):
        pass


class SungrowInverterSetup(ComponentSetup[SungrowInverterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SungrowInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowInverterConfiguration())
