from typing import Optional


class VWIdConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,        # show in UI
                 password: Optional[str] = None,       # show in UI
                 vin: Optional[str] = None,            # show in UI
                 refreshToken: Optional[str] = None,   # DON'T show in UI!
                 calculate_soc: bool = False           # show in UI
                 ):
        self.user_id = user_id
        self.password = password
        self.vin = vin
        self.refreshToken = refreshToken
        self.calculate_soc = calculate_soc


class VWId:
    def __init__(self,
                 name: str = "VWId",
                 type: str = "vwid",
                 official: bool = False,
                 configuration: VWIdConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or VWIdConfiguration()
