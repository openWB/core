from typing import Optional


class SampleTariffConfiguration:
    def __init__(self, ip_address: Optional[str] = None, password: Optional[str] = None):
        self.ip_address = ip_address
        self.password = password


class SampleTariff:
    def __init__(self,
                 name: str = "Sample",
                 type: str = "sample",
                 configuration: SampleTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SampleTariffConfiguration()
