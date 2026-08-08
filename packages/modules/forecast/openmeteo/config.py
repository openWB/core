from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class OpenMeteoForecastConfiguration:
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    forecast_hours: Optional[int] = None
    peak_power_kw: Optional[float] = None
    system_loss: Optional[float] = None
    irradiance_to_power_factor: Optional[float] = None
    strings: Optional[list[dict[str, Any]]] = None


@dataclass
class OpenMeteoForecast:
    name: str = "Open-Meteo PV Forecast"
    type: str = "openmeteo"
    official: bool = True
    configuration: OpenMeteoForecastConfiguration = field(default_factory=OpenMeteoForecastConfiguration)
