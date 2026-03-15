from typing import Optional


class SkodaConfiguration:
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


class Skoda:
    def __init__(self,
                 name: str = "Skoda",
                 type: str = "skoda",
                 official: bool = False,
                 configuration: SkodaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or SkodaConfiguration()
