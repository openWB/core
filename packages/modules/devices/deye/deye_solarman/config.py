from typing import Optional
from helpermodules.auto_str import auto_str

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class DeyeSolarmanConfiguration:
    def __init__(self,
                 ip_address: Optional[str] = None,
                 serial: int = None,
                 port: int = 8899,
                 modbus_id: int = 1):
        self.ip_address = ip_address
        self.serial = serial
        self.port = port
        self.modbus_id = modbus_id


class DeyeSolarman:
    def __init__(self,
                 name: str = "Deye/Jinko (Anbindung per LSW Dongle)",
                 type: str = "deye_solarman",
                 id: int = 0,
                 configuration: DeyeSolarmanConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or DeyeSolarmanConfiguration()


@auto_str
class DeyeSolarmanBatConfiguration:
    def __init__(self):
        pass


@auto_str
class DeyeSolarmanBatSetup(ComponentSetup[DeyeSolarmanBatConfiguration]):
    def __init__(self,
                 name: str = "Deye/Jinko Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: DeyeSolarmanBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or DeyeSolarmanBatConfiguration())


@auto_str
class DeyeSolarmanCounterConfiguration:
    def __init__(self):
        pass


@auto_str
class DeyeSolarmanCounterSetup(ComponentSetup[DeyeSolarmanCounterConfiguration]):
    def __init__(self,
                 name: str = "Deye/Jinko Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: DeyeSolarmanCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or DeyeSolarmanCounterConfiguration())


@auto_str
class DeyeSolarmanInverterConfiguration:
    def __init__(self):
        pass


@auto_str
class DeyeSolarmanInverterSetup(ComponentSetup[DeyeSolarmanInverterConfiguration]):
    def __init__(self,
                 name: str = "Deye/Jinko Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: DeyeSolarmanInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or DeyeSolarmanInverterConfiguration())
