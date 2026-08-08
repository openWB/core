from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class OpenMeteoForecastConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "Europe/Berlin"
    peak_power_kw: float = 9.5
    azimuth: float = 0.0
    tilt: float = 30.0
    system_loss: float = 0.14
    irradiance_to_power_factor: float = 0.2
    strings: Optional[list[dict[str, Any]]] = None


@dataclass
class OpenMeteoForecast:
    name: str = "Open-Meteo PV Forecast"
    type: str = "openmeteo"
    official: bool = True
    configuration: OpenMeteoForecastConfiguration = field(default_factory=OpenMeteoForecastConfiguration)
