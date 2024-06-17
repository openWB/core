from typing import Optional


class BMWbcConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 vin: Optional[str] = None,
                 calculate_soc: bool = False):
        self.user_id = user_id
        self.password = password
        self.vin = vin
        self.calculate_soc = calculate_soc


class BMWbc:
    def __init__(self,
                 name: str = "BMW (Bimmer)",
                 type: str = "bmwbc",
                 configuration: BMWbcConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or BMWbcConfiguration()
