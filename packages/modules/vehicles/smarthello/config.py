from typing import Optional


class SmartHelloConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 vin: Optional[str] = None,
                 sessioncache: Optional[str] = None) -> None:
        self.user_id = user_id
        self.password = password
        self.vin = vin
        self.sessioncache = sessioncache


class SmartHello:
    def __init__(self,
                 name: str = "Smart Hello (#1, #3)",
                 type: str = "smarthello",
                 configuration: SmartHelloConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SmartHelloConfiguration()
