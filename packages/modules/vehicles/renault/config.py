from typing import Optional


class RenaultConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 country: Optional[str] = None,
                 vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.country = country
        self.vin = vin


class Renault:
    def __init__(self,
                 name: str = "Renault",
                 type: str = "renault",
                 configuration: RenaultConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or RenaultConfiguration()
