from typing import Optional


class SmartEQConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,        # show in UI
                 password: Optional[str] = None,       # show in UI
                 vin: Optional[str] = None             # show in UI
                 # refreshToken: Optional[str] = None    # DON'T show in UI!
                 ):
        self.user_id = user_id
        self.password = password
        self.vin = vin
        # self.refreshToken = refreshToken


class SmartEQ:
    def __init__(self,
                 name: str = "SmartEQ",
                 type: str = "smarteq",
                 configuration: SmartEQConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SmartEQConfiguration()
