from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class Huawei_EmmaConfiguration:
    def __init__(self, modbus_id: int = 0,
                 ip_address: Optional[str] = None,
                 port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class Huawei_Emma:
    def __init__(self,
                 name: str = "Huawei EMMA",
                 type: str = "huawei_emma",
                 id: int = 0,
                 configuration: Huawei_EmmaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or Huawei_EmmaConfiguration()


class Huawei_EmmaBatConfiguration:
    def __init__(self):
        pass


class Huawei_EmmaBatSetup(ComponentSetup[Huawei_EmmaBatConfiguration]):
    def __init__(self,
                 name: str = "Huawei EMMA Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: Huawei_EmmaBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or Huawei_EmmaBatConfiguration())


class Huawei_EmmaCounterConfiguration:
    def __init__(self):
        pass


class Huawei_EmmaCounterSetup(ComponentSetup[Huawei_EmmaCounterConfiguration]):
    def __init__(self,
                 name: str = "Huawei EMMA Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: Huawei_EmmaCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or Huawei_EmmaCounterConfiguration())


class Huawei_EmmaInverterConfiguration:
    def __init__(self):
        pass


class Huawei_EmmaInverterSetup(ComponentSetup[Huawei_EmmaInverterConfiguration]):
    def __init__(self,
                 name: str = "Huawei EMMA Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: Huawei_EmmaInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or Huawei_EmmaInverterConfiguration())
