from typing import Optional

class BMWConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None, vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.vin = vin


class BMW:
    def __init__(self,
                 name: str = "BMW",
                 type: str = "bmw",
                 configuration: BMWConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or BMWConfiguration()
