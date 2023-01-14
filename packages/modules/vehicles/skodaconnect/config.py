from typing import Optional


class SkodaConnectConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,        # show in UI
                 password: Optional[str] = None,       # show in UI
                 vin: Optional[str] = None,            # show in UI
                 refreshToken: Optional[dict] = None   # DON'T show in UI!
                 ):
        self.user_id = user_id
        self.password = password
        self.vin = vin
        self.refreshToken = refreshToken


class SkodaConnect:
    def __init__(self,
                 name: str = "SkodaConnect",
                 type: str = "skodaconnect",
                 configuration: SkodaConnectConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SkodaConnectConfiguration()
