from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OpenMeteoForecastConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "Europe/Berlin"
    system_loss: float = 0.14
    strings: Optional[List] = None


@dataclass
class OpenMeteoForecast:
    name: str = "Open-Meteo PV Forecast"
    type: str = "openmeteo"
    official: bool = True
    configuration: OpenMeteoForecastConfiguration = field(default_factory=OpenMeteoForecastConfiguration)
