from dataclasses import dataclass


@dataclass
class BmwCardataConfiguration:
    client_id: str = ""
    vin: str = ""
    calculate_soc: bool = False
    test_mode: bool = True
    test_soc: int = 80
    test_range: int = 300
    access_token: str = ""
    refresh_token: str = ""
    expires_at: float = 0
    container_id: str = ""


@dataclass
class BmwCardataSetup:
    name: str = "BMW CarData"
    type: str = "bmw_cardata"
    official: bool = False
    configuration: BmwCardataConfiguration = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = BmwCardataConfiguration()
