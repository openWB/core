from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class BatKitConfiguration:
    def __init__(self):
        pass


class BatKitSetup:
    def __init__(self,
                 name: str = "openWB Speicher-Kit",
                 type: str = "openwb_bat_kit",
                 id: int = 0,
                 configuration: BatKitConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or BatKitConfiguration()


class BatKitBatConfiguration:
    def __init__(self, version: int = 2):
        self.version = version


class BatKitBatSetup(ComponentSetup[BatKitBatConfiguration]):
    def __init__(self,
                 name: str = "openWB Speicher-Kit",
                 type: str = "bat",
                 id: int = 0,
                 configuration: BatKitBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or BatKitBatConfiguration())
