from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class SiemensSentronConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class SiemensSentron:
    def __init__(self,
                 name: str = "Siemens Sentron",
                 type: str = "siemens_sentron",
                 id: int = 0,
                 configuration: SiemensSentronConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SiemensSentronConfiguration()


class SiemensSentronCounterConfiguration:
    def __init__(self):
        pass


class SiemensSentronCounterSetup(ComponentSetup[SiemensSentronCounterConfiguration]):
    def __init__(self,
                 name: str = "Siemens Sentron Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SiemensSentronCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SiemensSentronCounterConfiguration())


class SiemensSentronInverterConfiguration:
    def __init__(self):
        pass


class SiemensSentronInverterSetup(ComponentSetup[SiemensSentronInverterConfiguration]):
    def __init__(self,
                 name: str = "Siemens Sentron PV-Zähler",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SiemensSentronInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SiemensSentronInverterConfiguration())


class SiemensSentronBatConfiguration:
    def __init__(self):
        pass


class SiemensSentronBatSetup(ComponentSetup[SiemensSentronBatConfiguration]):
    def __init__(self,
                 name: str = "Siemens Sentron Speicher-Zähler",
                 type: str = "bat",
                 id: int = 0,
                 configuration: SiemensSentronBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SiemensSentronBatConfiguration())
