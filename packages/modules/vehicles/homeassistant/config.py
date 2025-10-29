from helpermodules.auto_str import auto_str
from typing import Optional


@auto_str
class HaVehicleSocConfiguration:
    def __init__(
            self,
            url: Optional[str] = None,
            token: Optional[str] = None
            ):
        self.url = url
        self.token = token


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
