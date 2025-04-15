from typing import Optional


class EVCCVehicleSocConfiguration:
    def __init__(self,
                 vehicle_id: Optional[int] = None,
                 sponsor_token: Optional[str] = None,
                 user_id: Optional[str] = None,
                 password: Optional[str] = None,
                 VIN: Optional[str] = "",
                 vehicle_type: Optional[str] = None,
                 calculate_soc: bool = False) -> None:
        self.vehicle_id = vehicle_id
        self.calculate_soc = calculate_soc
        self.user_id = user_id
        self.password = password
        self.sponsor_token = sponsor_token
        self.vehicle_type = vehicle_type
        self.VIN = VIN


class EVCCVehicleSoc:
    def __init__(self,
                 name: str = "EVCC",
                 type: str = "evcc",
                 official: bool = False,
                 configuration: EVCCVehicleSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or EVCCVehicleSocConfiguration()
