class MyskodaConfiguration:
    def __init__(self,
                 api_key: str = None,
                 vin: str = None) -> None:
        self.api_key = api_key
        self.vin = vin


class Myskoda:
    def __init__(self,
                 name: str = "MyŠkoda (Public API)",
                 type: str = "myskoda",
                 configuration: MyskodaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or MyskodaConfiguration()
