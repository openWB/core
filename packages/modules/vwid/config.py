from typing import Optional


class VWIdConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None, vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.vin = vin


class VWId:
    def __init__(self,
                 name: str = "VWId",
                 type: str = "vwid",
                 configuration: VWIdConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or VWIdConfiguration()
