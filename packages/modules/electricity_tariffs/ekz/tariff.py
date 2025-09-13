#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
from dateutil import tz
from urllib.parse import quote
from typing import Dict
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.ekz.config import EkzTariffConfiguration
from modules.electricity_tariffs.ekz.config import EkzTariff

# Combine power and grid prices, convert to kWh
def addPrices (power: dict, grid: dict) -> tuple[str, float]:
    timestamp = str(int(datetime.strptime(power['start_timestamp'],"%Y-%m-%dT%H:%M:%S%z")\
                    .astimezone(tz.tzutc()).timestamp()))
    power_price = power['electricity'][1]['value']
    grid_price = grid['grid'][0]['value']
    return (timestamp, (power_price+grid_price)/1000)

# Read prices from EKZ API
def readApi() -> list[tuple[str, float]]:
    endpoint="https://api.tariffs.ekz.ch/v1/tariffs"
    tariff_power="electricity_dynamic"
    tariff_grid="grid_400D_inclFees"
    utcnow = datetime.now(timezone.utc)
    startDate = quote(utcnow.strftime("%Y-%m-%dT%H:00:00Z"))
    endDate = quote((utcnow + timedelta(days=2)).strftime("%Y-%m-%dT%H:00:00Z")) 
    session=req.get_http_session()
    power_raw = session.get(
        url=endpoint +
            f"?tariff_name={tariff_power}&start_timestamp={startDate}&end_timestamp={endDate}",
        ).json()["prices"]
    grid_raw = session.get(
        url=endpoint +
            f"?tariff_name={tariff_grid}&start_timestamp={startDate}&end_timestamp={endDate}",
        ).json()["prices"]
    return list(map(addPrices, power_raw, grid_raw))

# Aggregate 15min prices to hourly prices by taking the maximum price in each hour
def aggregatePrices (quarterlyPrices) -> list[tuple[str, float]]:
    hourlyPrices = []
    currentHourPrices = []
    currentTimestamp = 0
    for p in quarterlyPrices:
        time = datetime.fromtimestamp(int(p[0]))
        if time.minute == 0:
            if len(currentHourPrices) > 0:
                hourlyPrices.append((currentTimestamp, max(currentHourPrices)))
                currentHourPrices = []
            currentTimestamp = p[0]
        else:
            currentHourPrices.append(p[1])
    if len(currentHourPrices) > 0:
        hourlyPrices.append((currentTimestamp, max(currentHourPrices)))
    return hourlyPrices

def fetch_prices (config: EkzTariffConfiguration) -> Dict[str, float]:
    # Fetch electricity prices from EKZ API
    # API Reference: https://api.tariffs.ekz.ch/swagger
    pricelist = readApi()
    hourly_list = aggregatePrices(pricelist)
    prices: Dict[str, float] = dict(hourly_list)
    return prices

def create_electricity_tariff(config: EkzTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=EkzTariff)
