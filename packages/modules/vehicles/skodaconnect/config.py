from typing import Optional


class SkodaConnectConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None, vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.vin = vin


class SkodaConnect:
    def __init__(self,
                 name: str = "SkodaConnect",
                 type: str = "skodaconnect",
                 configuration: SkodaConnectConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SkodaConnectConfiguration()
