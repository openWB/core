from typing import Optional


class BMWbcConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 vin: Optional[str] = None,
                 captcha_token: Optional[str] = None,
                 calculate_soc: bool = False):
        self.user_id = user_id
        self.password = password
        self.vin = vin
        self.captcha_token = captcha_token
        self.calculate_soc = calculate_soc


class BMWbc:
    def __init__(self,
                 name: str = "BMW & Mini ",
                 type: str = "bmwbc",
                 official: bool = False,
                 configuration: BMWbcConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or BMWbcConfiguration()
