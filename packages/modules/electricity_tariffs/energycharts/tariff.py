from dataclasses import dataclass
from typing import Dict
from datetime import datetime
import json
import urllib.request

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariffConfiguration
from modules.electricity_tariffs.energycharts.config import EnergyChartsTariff


@dataclass
class CountryData:
    url: str


def fetch_prices(config: EnergyChartsTariffConfiguration) -> Dict[int, float]:
    country_code: CountryData = globals()[config.country]
    current_dateTime = datetime.now().replace(microsecond=0)
    start_time = current_dateTime.strftime("%Y-%m-%d") + 'T00%3A00%2B01%3A00'
    end_time = current_dateTime.strftime("%Y-%m-%d") + 'T23%3A45%2B01%3A00'
    value = 'price'
    URL = 'https://api.energy-charts.info/' + value + '?bzn=' + country_code + '&start='
    + start_time + '&end=' + end_time
    a = urllib.request.urlopen(URL)
    raw_prices = json.loads(a.read().decode())

    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["price"]/1000000  # €/MWh -> €/Wh
        timestamp = data["unix_seconds"]/1000  # Epoch from ms in s
        prices.update({int(timestamp): formatted_price})
    return prices


def create_electricity_tariff(config: EnergyChartsTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return ConfigurableElectricityTariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=EnergyChartsTariff)
