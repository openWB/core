from typing import Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.sungrow.sungrow_sh.version import Version
from ..vendor import vendor_descriptor


class SungrowSHConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1,
                 version: Version = Version.SH):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id
        self.version = version


class SungrowSH:
    def __init__(self,
                 name: str = "Sungrow SH",
                 type: str = "sungrow_sh",
                 id: int = 0,
                 configuration: SungrowSHConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SungrowSHConfiguration()


class SungrowSHBatConfiguration:
    def __init__(self):
        pass


class SungrowSHBatSetup(ComponentSetup[SungrowSHBatConfiguration]):
    def __init__(self,
                 name: str = "Sungrow SH Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SungrowSHBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowSHBatConfiguration())


class SungrowSHCounterConfiguration:
    def __init__(self):
        pass


class SungrowSHCounterSetup(ComponentSetup[SungrowSHCounterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow SH Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SungrowSHCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowSHCounterConfiguration())


class SungrowSHInverterConfiguration:
    def __init__(self):
        pass


class SungrowSHInverterSetup(ComponentSetup[SungrowSHInverterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow SH Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SungrowSHInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowSHInverterConfiguration())
