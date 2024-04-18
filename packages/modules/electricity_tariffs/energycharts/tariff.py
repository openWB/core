from dataclasses import dataclass
from typing import Dict
from datetime import datetime, timedelta
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


current_dateTime = datetime.now()
tomorrow = datetime.now() + timedelta(1)
# start_time = current_dateTime.strftime("%Y-%m-%d") + 'T' + current_dateTime.strftime("%H") + '%3A'
# + current_dateTime.strftime("%M") + '%2B01%3A00'
start_time = current_dateTime.strftime("%Y-%m-%d") + 'T00%3A00%2B01%3A00'
end_time = tomorrow.strftime("%Y-%m-%d") + 'T23%3A59%2B01%3A00'
value = 'price'
de = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=DE-LU' + '&start='
                 + start_time + '&end=' + end_time)
at = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=AT' + '&start='
                 + start_time + '&end=' + end_time)
be = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=BE' + '&start='
                 + start_time + '&end=' + end_time)
bg = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=BG' + '&start='
                 + start_time + '&end=' + end_time)
ch = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=CH' + '&start='
                 + start_time + '&end=' + end_time)
cz = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=CZ' + '&start='
                 + start_time + '&end=' + end_time)
dk1 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=DK1' + '&start='
                  + start_time + '&end=' + end_time)
dk2 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=DK2' + '&start='
                  + start_time + '&end=' + end_time)
ee = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=EE' + '&start='
                 + start_time + '&end=' + end_time)
es = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=ES' + '&start='
                 + start_time + '&end=' + end_time)
fi = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=FI' + '&start='
                 + start_time + '&end=' + end_time)
fr = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=FR' + '&start='
                  + start_time + '&end=' + end_time)
gr = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=GR' + '&start='
                 + start_time + '&end=' + end_time)
hr = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=HR' + '&start='
                 + start_time + '&end=' + end_time)
hu = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=HU' + '&start='
                 + start_time + '&end=' + end_time)
itCAL = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-Calabria' + '&start='
                    + start_time + '&end=' + end_time)
itCN = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-Centre-North' + '&start='
                   + start_time + '&end=' + end_time)
itCS = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-Centre-South' + '&start='
                   + start_time + '&end=' + end_time)
itN = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-North' + '&start='
                  + start_time + '&end=' + end_time)
itSAC = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-SACOAC' + '&start='
                    + start_time + '&end=' + end_time)
itSDC = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-SACODC' + '&start='
                    + start_time + '&end=' + end_time)
itSA = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-Sardinia' + '&start='
                   + start_time + '&end=' + end_time)
itSI = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-Sicily' + '&start='
                   + start_time + '&end=' + end_time)
itS = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=IT-South' + '&start='
                  + start_time + '&end=' + end_time)
lt = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=LT' + '&start='
                 + start_time + '&end=' + end_time)
lv = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=LV' + '&start='
                 + start_time + '&end=' + end_time)
me = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=ME' + '&start='
                 + start_time + '&end=' + end_time)
nl = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NL' + '&start='
                 + start_time + '&end=' + end_time)
no1 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NO1' + '&start='
                  + start_time + '&end=' + end_time)
no2 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NO2' + '&start='
                  + start_time + '&end=' + end_time)
no2NSL = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NO2NSL' + '&start='
                     + start_time + '&end=' + end_time)
no3 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NO3' + '&start='
                  + start_time + '&end=' + end_time)
no4 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NO4' + '&start='
                  + start_time + '&end=' + end_time)
no5 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=NO5' + '&start='
                  + start_time + '&end=' + end_time)
pl = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=PL' + '&start='
                 + start_time + '&end=' + end_time)
pt = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=PT' + '&start='
                 + start_time + '&end=' + end_time)
ro = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=RO' + '&start='
                 + start_time + '&end=' + end_time)
rs = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=RS' + '&start='
                 + start_time + '&end=' + end_time)
se1 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=SE1' + '&start='
                  + start_time + '&end=' + end_time)
se2 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=SE2' + '&start='
                  + start_time + '&end=' + end_time)
se3 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=SE3' + '&start='
                  + start_time + '&end=' + end_time)
se4 = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=SE4' + '&start='
                  + start_time + '&end=' + end_time)
si = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=SI' + '&start='
                 + start_time + '&end=' + end_time)
sk = CountryData(url='https://api.energy-charts.info/' + value + '?bzn=SK' + '&start='
                 + start_time + '&end=' + end_time)


def fetch_prices(config: EnergyChartsTariffConfiguration) -> Dict[int, float]:
    country_data: CountryData = globals()[config.country]
    addPrice = config.servePrice
    a = urllib.request.urlopen(country_data.url)
    raw_prices = json.loads(a.read().decode())
    time_stamp_arr = []
    price_arr = []
    for unix_sec in raw_prices['unix_seconds']:
        time_stamp_arr.append(unix_sec)  # Epoch from ms in s
    for x in raw_prices['price']:
        price_arr.append((float(x + (addPrice*10))/1000000))  # €/MWh -> €/Wh + Aufschlag
    prices: Dict[int, float] = {}
    prices = dict(zip(time_stamp_arr, price_arr))
    return prices


def create_electricity_tariff(config: EnergyChartsTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return ConfigurableElectricityTariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=EnergyChartsTariff)
