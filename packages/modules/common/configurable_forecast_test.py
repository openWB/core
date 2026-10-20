from unittest.mock import Mock

from modules.common.component_state import ForecastState
from modules.common.configurable_forecast import ConfigurableForecast
from modules.forecast.open_meteo.config import OpenMeteoForecast


def _make_forecast() -> ConfigurableForecast:
    # strings=[] -> Konfiguration unvollständig, _is_update_due() bleibt False
    return ConfigurableForecast(OpenMeteoForecast(), Mock(return_value=Mock(return_value=ForecastState())))


def test_store_update_runs_even_when_no_fetch_is_due():
    forecast = _make_forecast()
    forecast.store = Mock()

    forecast.update()

    forecast.store.update.assert_called_once()
    forecast.store.set.assert_not_called()
    forecast._component_updater.assert_not_called()
