from helpermodules.auto_str import auto_str


@auto_str
class HttpSocConfiguration:
    def __init__(self, soc_url=None,
                 range_url=None,
                 calculate_soc: bool = False):
        self.soc_url = soc_url
        self.range_url = range_url
        self.calculate_soc = calculate_soc


@auto_str
class HttpSocSetup():
    def __init__(self,
                 name: str = "HTTP SOC Module",
                 type: str = "http",
                 official: bool = True,
                 configuration: HttpSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or HttpSocConfiguration()
