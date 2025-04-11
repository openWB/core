from typing import Optional


class TronityVehicleSocConfiguration:
    def __init__(self,
                 vehicle_id: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 access_token: Optional[str] = None,
                 calculate_soc: bool = False) -> None:
        self.vehicle_id = vehicle_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.calculate_soc = calculate_soc


class TronityVehicleSoc:
    def __init__(self,
                 name: str = "Tronity",
                 type: str = "tronity",
                 official: bool = True,
                 configuration: TronityVehicleSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or TronityVehicleSocConfiguration()
