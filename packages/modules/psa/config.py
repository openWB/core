from typing import Optional


class PSAConfiguration:
    def __init__(self,
                 userid: Optional[str] = "uid",
                 password: Optional[str] = "pwd",
                 client_id: Optional[str] = "clid",
                 client_secret: Optional[str] = "clsc",
                 manufacturer: Optional[str] = "Peugeot",
                 soccalc: Optional[str] = "0",
                 vin: Optional[str] = "PSA1234"):
        self.userid = userid
        self.password = password
        self.client_id = client_id
        self.client_secret = client_secret
        self.manufacturer = manufacturer
        self.soccalc = soccalc
        self.vin = vin


class PSA:
    def __init__(self,
                 name: str = "PSA",
                 type: str = "psa",
                 configuration: PSAConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or PSAConfiguration()
