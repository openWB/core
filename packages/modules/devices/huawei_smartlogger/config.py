from typing import Optional
from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup

@auto_str
class Huawei_SmartloggerConfiguration:
    def __init__(self,ip_address: Optional[str] = None):
        self.ip_address = ip_address
        

@auto_str
class Huawei_Smartlogger:
    def __init__(self,
                 name: str = "Huawei_Smartlogger",
                 type: str = "huawei_smartlogger",
                 id: int = 0,
                 configuration: Huawei_SmartloggerConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or Huawei_SmartloggerConfiguration()

@auto_str
class Huawei_SmartloggerBatConfiguration:
    def __init__(self,modbus_id:int=4):
        self.modbus_id=modbus_id
        pass
@auto_str
class Huawei_SmartloggerBatSetup(ComponentSetup[Huawei_SmartloggerBatConfiguration]):
    def __init__(self,
                 name: str = " Huawei Luna",
                 type: str = "bat",
                 id: int = 0,
                 configuration: Huawei_SmartloggerBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or Huawei_SmartloggerBatConfiguration())
        
@auto_str      
class Huawei_SmartloggerCounterConfiguration:
    def __init__(self,modbus_id:int=3):
        self.modbus_id=modbus_id
        pass
@auto_str
class Huawei_SmartloggerCounterSetup(ComponentSetup[Huawei_SmartloggerCounterConfiguration]):
    def __init__(self,
                 name: str = "Huawei Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: Huawei_SmartloggerCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or Huawei_SmartloggerCounterConfiguration())

@auto_str
class Huawei_SmartloggerInverterConfiguration:
    def __init__(self,modbus_id:int=1):
        self.modbus_id=modbus_id
        pass
@auto_str
class Huawei_SmartloggerInverterSetup(ComponentSetup[Huawei_SmartloggerInverterConfiguration]):
    def __init__(self,
                 name: str = "Huawei Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: Huawei_SmartloggerInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or Huawei_SmartloggerInverterConfiguration())
