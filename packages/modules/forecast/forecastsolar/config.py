from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ForecastSolarConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    peak_power_kw: float = 9.5
    azimuth: float = 0.0
    tilt: float = 30.0
    strings: Optional[list[dict[str, Any]]] = None


@dataclass
class ForecastSolar:
    name: str = "Forecast.Solar"
    type: str = "forecastsolar"
    official: bool = True
    configuration: ForecastSolarConfiguration = field(default_factory=ForecastSolarConfiguration)
