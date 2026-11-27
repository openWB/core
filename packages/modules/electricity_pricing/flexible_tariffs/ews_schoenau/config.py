from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EwsSchoenauTariffConfiguration:
    api_key: Optional[str] = field(default=None, repr=False)


@dataclass
class EwsSchoenauTariff:
    name: str = "EWS Schönau Ökostrom Dynamisch"
    type: str = "ews_schoenau"
    official: bool = False
    configuration: EwsSchoenauTariffConfiguration = field(default_factory=EwsSchoenauTariffConfiguration)
