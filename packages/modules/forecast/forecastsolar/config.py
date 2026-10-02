from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ForecastSolarConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    api_key: Optional[str] = None
    strings: Optional[List] = None


@dataclass
class ForecastSolar:
    name: str = "Forecast.Solar"
    type: str = "forecastsolar"
    official: bool = True
    configuration: ForecastSolarConfiguration = field(default_factory=ForecastSolarConfiguration)
