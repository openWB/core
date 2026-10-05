from dataclasses import dataclass, field
from typing import List, Optional, TypedDict
from dataclasses import field


class ForecastSolarStringConfiguration(TypedDict):
    name: Optional[str]
    peak_power_kw: float
    tilt: float
    azimuth: float


@dataclass
class ForecastSolarConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    api_key: Optional[str] = None
    strings: List[ForecastSolarStringConfiguration] = field(default_factory=list)


@dataclass
class ForecastSolar:
    name: str = "Forecast.Solar"
    type: str = "forecast_solar"
    official: bool = False
    configuration: ForecastSolarConfiguration = field(default_factory=ForecastSolarConfiguration)
