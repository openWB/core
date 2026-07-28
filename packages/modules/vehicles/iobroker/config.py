from helpermodules.auto_str import auto_str
from typing import Optional


@auto_str
class IoBrokerSocConfiguration:
    def __init__(
            self,
            calculate_soc: bool = False,
            url: Optional[str] = None,
            user: Optional[str] = None,
            password: Optional[str] = None,
            state_soc: Optional[str] = None,
            state_range: Optional[str] = None,
            state_odometer: Optional[str] = None,
            timeout: int = 5
            ):
        self.calculate_soc = calculate_soc
        self.url = url
        self.user = user
        self.password = password
        self.state_soc = state_soc
        self.state_range = state_range
        self.state_odometer = state_odometer
        self.timeout = timeout


@auto_str
class IoBrokerSocSetup():
    def __init__(self,
                 name: str = "ioBroker",
                 type: str = "iobroker",
                 official: bool = False,
                 configuration: IoBrokerSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or IoBrokerSocConfiguration()
