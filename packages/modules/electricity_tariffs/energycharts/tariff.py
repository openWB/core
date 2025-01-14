from typing import Dict
from datetime import datetime, timedelta

from helpermodules import timecheck

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariffConfiguration
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariff


def fetch_prices(config: EnergyChartsTariffConfiguration) -> Dict[int, float]:
    tomorrow = datetime.now() + timedelta(1)
    start_time = timecheck.create_unix_timestamp_current_full_hour()
    end_time = int(tomorrow.timestamp())
    url = f'https://api.energy-charts.info/price?bzn={config.country}&start={start_time}&end={end_time}'
    raw_prices = req.get_http_session().get(url).json()
    price_arr = []
    for price in raw_prices['price']:
        price_arr.append((float(price + (config.surcharge*10))/1000000))  # €/MWh -> €/Wh + Aufschlag
    prices: Dict[int, float] = {}
    prices = dict(zip([str(int(unix_seconds)) for unix_seconds in raw_prices['unix_seconds']], price_arr))
    return prices


def create_electricity_tariff(config: EnergyChartsTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=EnergyChartsTariff)
