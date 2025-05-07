from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class KacoConfiguration:
    def __init__(self,
                 port: int = 502,
                 ip_address=None):
        self.port = port
        self.ip_address = ip_address


class Kaco:
    def __init__(self,
                 name: str = "Kaco Tx1 & Tx3 Serie",
                 type: str = "kaco_tx",
                 id: int = 0,
                 configuration:  KacoConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or KacoConfiguration()


class KacoInverterConfiguration:
    def __init__(self, modbus_id: int = 1):
        self.modbus_id = modbus_id


class KacoInverterSetup(ComponentSetup[KacoInverterConfiguration]):
    def __init__(self,
                 name: str = "Kaco Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: KacoInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or KacoInverterConfiguration())
