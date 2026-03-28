from helpermodules.auto_str import auto_str


@auto_str
class BmwCardataConfiguration:
    def __init__(
        self,
        client_id: str = None,
        vin: str = None,
        calculate_soc: bool = False,
        test_mode: bool = False,
        test_soc: int = 80,
        test_range: int = 300,
    ):
        self.client_id = client_id
        self.vin = vin
        self.calculate_soc = calculate_soc
        self.test_mode = test_mode
        self.test_soc = test_soc
        self.test_range = test_range


@auto_str
class BmwCardataSetup:
    def __init__(
        self,
        name: str = "BMW CarData",
        type: str = "bmw_cardata",
        official: bool = False,
        configuration: BmwCardataConfiguration = None,
    ) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or BmwCardataConfiguration()