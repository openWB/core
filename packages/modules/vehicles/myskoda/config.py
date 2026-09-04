from dataclasses import dataclass


@dataclass
class MyskodaConfiguration:
    api_key: str = ""
    vin: str = ""
    # wird vom Backend nach jedem erfolgreichen Abruf aus dem API-Response-Header
    # zurückgeschrieben (ISO-8601), nicht vom Nutzer editierbar - siehe soc.py
    key_expires_at: str = ""


@dataclass
class Myskoda:
    name: str = "MyŠkoda (Public API)"
    type: str = "myskoda"
    official: bool = False
    configuration: MyskodaConfiguration = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = MyskodaConfiguration()
