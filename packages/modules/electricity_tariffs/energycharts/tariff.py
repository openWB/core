from typing import Dict
from datetime import datetime, timedelta
from modules.common import req
import pytz

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariffConfiguration
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariff


def fetch_prices(config: EnergyChartsTariffConfiguration) -> Dict[int, float]:
    current_dateTime = datetime.now()
    tomorrow = datetime.now() + timedelta(1)
    if datetime.today().astimezone(pytz.timezone("Europe/Berlin")).dst().total_seconds()/3600:
        # UTC Zeit +02:00 = '%2B02%3A00'
        start_time = current_dateTime.strftime("%Y-%m-%d") + 'T' + current_dateTime.strftime("%H") + \
            '%3A00' + '%2B02%3A00'
    else:
        # UTC Zeit +01:00 = '%2B01%3A00'
        start_time = current_dateTime.strftime("%Y-%m-%d") + 'T' + current_dateTime.strftime("%H") + \
            '%3A00' + '%2B01%3A00'
    end_time = tomorrow.strftime("%Y-%m-%d") + 'T23%3A59%2B01%3A00'
    url = f'https://api.energy-charts.info/price?bzn={config.country}&start={start_time}&end={end_time}'
    raw_prices = req.get_http_session().get(url).json()
    price_arr = []
    for price in raw_prices['price']:
        price_arr.append((float(price + (config.surcharge*10))/1000000))  # €/MWh -> €/Wh + Aufschlag
    prices: Dict[int, float] = {}
    prices = dict(zip(raw_prices['unix_seconds'], price_arr))
    return prices


def create_electricity_tariff(config: EnergyChartsTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=EnergyChartsTariff)
