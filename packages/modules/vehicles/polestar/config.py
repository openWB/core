from typing import Optional


class Polestar2Configuration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None, vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.vin = vin


class Polestar2:
    def __init__(self,
                 name: str = "Polestar2",
                 type: str = "polestar",
                 official: bool = False,
                 configuration: Polestar2Configuration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or Polestar2Configuration()
