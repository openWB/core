from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class EcoflowStreamConfiguration:
    def __init__(self,
                 serial=None,
                 access_key=None,
                 secret_key=None):
        self.serial = serial
        self.access_key = access_key
        self.secret_key = secret_key


class EcoflowStream:

    def __init__(self,
                 name: str = "Ecoflow Stream",
                 type: str = "stream",
                 id: int = 0,
                 configuration: EcoflowStreamConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or EcoflowStreamConfiguration()


class EcoflowStreamBatConfiguration:
    def __init__(self):
        pass


class EcoflowStreamBatSetup(ComponentSetup[EcoflowStreamBatConfiguration]):
    def __init__(self,
                 name: str = "Ecoflow Stream Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: EcoflowStreamBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or EcoflowStreamBatConfiguration())


class EcoflowStreamCounterConfiguration:
    def __init__(self):
        pass


class EcoflowStreamCounterSetup(ComponentSetup[EcoflowStreamCounterConfiguration]):
    def __init__(self,
                 name: str = "Ecoflow Stream Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: EcoflowStreamCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or EcoflowStreamCounterConfiguration())


class EcoflowStreamInverterConfiguration:
    def __init__(self):
        pass


class EcoflowStreamInverterSetup(ComponentSetup[EcoflowStreamInverterConfiguration]):
    def __init__(self,
                 name: str = "Ecoflow Stream Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: EcoflowStreamInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or EcoflowStreamInverterConfiguration())
