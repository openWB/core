from helpermodules.auto_str import auto_str
from typing import Optional


@auto_str
class HaVehicleSocConfiguration:
    def __init__(
            self,
            calculate_soc: bool = False,
            url: Optional[str] = None,
            token: Optional[str] = None,
            entity_soc: Optional[str] = None,
            entity_range: Optional[str] = None,
            entity_odometer: Optional[str] = None
            ):
        self.calculate_soc = calculate_soc
        self.url = url
        self.token = token
        self.entity_soc = entity_soc
        self.entity_range = entity_range
        self.entity_odometer = entity_odometer


@auto_str
class HaVehicleSocSetup():
    def __init__(self,
                 name: str = "HomeAssistant",
                 type: str = "homeassistant",
                 official: bool = True,
                 configuration: HaVehicleSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or HaVehicleSocConfiguration()
