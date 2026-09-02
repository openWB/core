class MyskodaConfiguration:
    def __init__(self,
                 api_key: str = None,
                 vin: str = None,
                 sandbox: bool = False) -> None:
        self.api_key = api_key
        self.vin = vin
        # sandbox=True nutzt public.test-api.connect.skoda-auto.cz statt der Produktiv-API
        self.sandbox = sandbox


class Myskoda:
    def __init__(self,
                 name: str = "MyŠkoda (Public API)",
                 type: str = "myskoda",
                 configuration: MyskodaConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or MyskodaConfiguration()
