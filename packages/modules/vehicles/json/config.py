from helpermodules.auto_str import auto_str
from typing import Optional


@auto_str
class JsonSocConfiguration:
    def __init__(
            self,
            url: Optional[str] = None,
            soc_pattern: Optional[str] = None,
            range_pattern: Optional[str] = None,
            timestamp_pattern: Optional[str] = None,
            timeout: Optional[int] = None,
            calculate_soc: bool = False
            ):
        self.url = url
        self.soc_pattern = soc_pattern
        self.range_pattern = range_pattern
        self.timestamp_pattern = timestamp_pattern
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
