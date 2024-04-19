from typing import Dict
from datetime import datetime, timedelta
import json
import urllib.request

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariffConfiguration
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariff


def fetch_prices(config: EnergyChartsTariffConfiguration) -> Dict[int, float]:
    current_dateTime = datetime.now()
    tomorrow = datetime.now() + timedelta(1)
    start_time = current_dateTime.strftime("%Y-%m-%d") + 'T00%3A00%2B01%3A00'
    end_time = tomorrow.strftime("%Y-%m-%d") + 'T23%3A59%2B01%3A00'
    url = f'https://api.energy-charts.info/price?bzn={config.country}&start={start_time}&end={end_time}'
    add_price = config.serve_price
    a = urllib.request.urlopen(url)
    raw_prices = json.loads(a.read().decode())
    time_stamp_arr = []
    price_arr = []
    for unix_sec in raw_prices['unix_seconds']:
        time_stamp_arr.append(unix_sec)  # Epoch from ms in s
    for price in raw_prices['price']:
        price_arr.append((float(price + (add_price*10))/1000000))  # €/MWh -> €/Wh + Aufschlag
    prices: Dict[int, float] = {}
    prices = dict(zip(time_stamp_arr, price_arr))
    return prices


def create_electricity_tariff(config: EnergyChartsTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return ConfigurableElectricityTariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=EnergyChartsTariff)
