from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ForecastSolarConfiguration:
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    peak_power_kw: Optional[float] = None
    azimuth: Optional[float] = None
    tilt: Optional[float] = None
    loss: Optional[float] = None
    horizon: Optional[str] = None
    output: Optional[str] = None
    strings: Optional[list[dict[str, Any]]] = None


@dataclass
class ForecastSolar:
    name: str = "Forecast.Solar"
    type: str = "forecastsolar"
    official: bool = True
    configuration: ForecastSolarConfiguration = field(default_factory=ForecastSolarConfiguration)
