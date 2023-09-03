from typing import Optional


class KIAConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None,
                 pin: Optional[str] = None, vin: Optional[str] = None):

        self.user_id = user_id
        self.password = password
        self.pin = pin
        self.vin = vin


class KIA:
    def __init__(self,
                 name: str = "KIA / Hyundai (experimental)",
                 type: str = "kia",
                 configuration: KIAConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or KIAConfiguration()
