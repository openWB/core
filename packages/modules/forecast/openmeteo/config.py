from dataclasses import dataclass, field


@dataclass
class OpenMeteoForecastConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = ""
    peak_power_kw: float = 0.0
    system_loss: float = 0.0
    irradiance_to_power_factor: float = 0.0


@dataclass
class OpenMeteoForecast:
    name: str = "Open-Meteo PV Forecast"
    type: str = "openmeteo"
    official: bool = True
    configuration: OpenMeteoForecastConfiguration = field(default_factory=OpenMeteoForecastConfiguration)
