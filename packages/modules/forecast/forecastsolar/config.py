from dataclasses import dataclass, field


@dataclass
class ForecastSolarConfiguration:
    latitude: float = 0.0
    longitude: float = 0.0
    peak_power_kw: float = 0.0
    azimuth: float = 0.0
    tilt: float = 0.0


@dataclass
class ForecastSolar:
    name: str = "Forecast.Solar"
    type: str = "forecastsolar"
    official: bool = True
    configuration: ForecastSolarConfiguration = field(default_factory=ForecastSolarConfiguration)
