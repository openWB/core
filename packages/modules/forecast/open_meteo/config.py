from dataclasses import dataclass, field
from typing import List, TypedDict, Optional


class StringConfiguration(TypedDict):
    name: Optional[str]
    peak_power_kw: float
    tilt: float
    azimuth: float


@dataclass
class OpenMeteoForecastConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "Europe/Berlin"
    system_loss: float = 0.14
    strings: List[StringConfiguration] = field(default_factory=list)


@dataclass
class OpenMeteoForecast:
    name: str = "Open-Meteo PV Forecast"
    type: str = "open_meteo"
    official: bool = False
    configuration: OpenMeteoForecastConfiguration = field(default_factory=OpenMeteoForecastConfiguration)
