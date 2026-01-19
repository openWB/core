from typing import Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.sungrow.sungrow_ihm.version import Version
from ..vendor import vendor_descriptor


class SungrowIHMConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 port: int = 502,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.modbus_id = modbus_id


class SungrowIHM:
    def __init__(self,
                 name: str = "Sungrow iHomeManager",
                 type: str = "sungrow_ihm",
                 id: int = 0,
                 configuration: SungrowIHMConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or SungrowIHMConfiguration()


class SungrowIHMBatConfiguration:
    def __init__(self):
        pass


class SungrowIHMBatSetup(ComponentSetup[SungrowIHMBatConfiguration]):
    def __init__(self,
                 name: str = " iHM Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: IHMBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowIHMBatConfiguration())


class SungrowIHMCounterConfiguration:
    def __init__(self):
        pass


class SungrowIHMCounterSetup(ComponentSetup[SungrowIHMCounterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow iHM Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: SungrowIHMCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowIHMCounterConfiguration())


class SungrowIHMInverterConfiguration:
    def __init__(self):
        pass


class SungrowIHMInverterSetup(ComponentSetup[SungrowIHMInverterConfiguration]):
    def __init__(self,
                 name: str = "Sungrow iHM Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: SungrowIHMInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or SungrowIHMInverterConfiguration())
