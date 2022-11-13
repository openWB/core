from typing import Optional


class RENAULTConfiguration:
    def __init__(self,
                 userid: Optional[str] = None,
                 password: Optional[str] = None,
                 location: Optional[str] = None,
                 country: Optional[str] = None,
                 vin: Optional[str] = None):
        self.userid = userid
        self.password = password
        self.location = location
        self.country = country
        self.vin = vin


class RENAULT:
    def __init__(self,
                 name: str = "RENAULT",
                 type: str = "renault",
                 configuration: RENAULTConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or RENAULTConfiguration()
