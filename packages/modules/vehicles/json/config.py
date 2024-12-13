from helpermodules.auto_str import auto_str


@auto_str
class JsonSocConfiguration:
    def __init__(self, soc_url=None, range_url=None, soc_pattern=None, range_pattern=None):
        self.soc_url = soc_url
        self.soc_pattern = soc_pattern
        self.range_url = range_url
        self.range_pattern = range_pattern


@auto_str
class JsonSocSetup():
    def __init__(self,
                 name: str = "JSON",
                 type: str = "json",
                 configuration: JsonSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or JsonSocConfiguration()
