from typing import Optional


class PSAConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 manufacturer: Optional[str] = None,
                 calculate_soc: bool = False,
                 vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.manufacturer = manufacturer
        self.calculate_soc = calculate_soc
        self.vin = vin


class PSA:
    def __init__(self,
                 name: str = "PSA",
                 type: str = "psa",
                 configuration: PSAConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or PSAConfiguration()
