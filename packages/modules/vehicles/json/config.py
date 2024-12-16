from helpermodules.auto_str import auto_str


@auto_str
class JsonSocConfiguration:
    def __init__(
            self,
            soc_url: str = None,
            range_url: str = None,
            soc_pattern: str = None,
            range_pattern: str = None,
            timeout: int = None,
            calculate_soc: bool = False
            ):
        self.soc_url = soc_url
        self.soc_pattern = soc_pattern
        self.range_url = range_url
        self.range_pattern = range_pattern
        self.timeout = timeout
        self.calculate_soc = calculate_soc


@auto_str
class JsonSocSetup():
    def __init__(self,
                 name: str = "JSON",
                 type: str = "json",
                 configuration: JsonSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or JsonSocConfiguration()
