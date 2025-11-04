#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
from dateutil import tz
from urllib.parse import quote
from typing import Dict
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.dynamic_tariffs.ekz.config import EkzTariffConfiguration
from modules.electricity_tariffs.dynamic_tariffs.ekz.config import EkzTariff


# Extract timestamp from power price entry
def timestamp(power):
    return str(int(datetime.strptime(power['start_timestamp'], "%Y-%m-%dT%H:%M:%S%z")
                   .astimezone(tz.tzutc()).timestamp()))


# Read prices from EKZ API
def readApi() -> list[tuple[str, float]]:
    endpoint = "https://api.tariffs.ekz.ch/v1/tariffs"
    tariff_power = "electricity_dynamic"
    tariff_grid = "grid_400D_inclFees"
    utcnow = datetime.now(timezone.utc)
    startDate = utcnow.strftime("%Y-%m-%dT%H:00:00Z")
    endDate = (utcnow + timedelta(days=2)).strftime("%Y-%m-%dT%H:00:00Z")
    session = req.get_http_session()
    power_raw = session.get(
        url=endpoint +
        f"?tariff_name={tariff_power}&start_timestamp={quote(startDate)}&end_timestamp={quote(endDate)}",
    ).json()["prices"]
    grid_raw = session.get(
        url=endpoint +
        f"?tariff_name={tariff_grid}&start_timestamp={quote(startDate)}&end_timestamp={quote(endDate)}",
    ).json()["prices"]
    return [(timestamp(power), (power['electricity'][1]['value']+grid['grid'][1]['value'])/1000)
            for power, grid in zip(power_raw, grid_raw)]


# Fetch electricity prices from EKZ API
# API Reference: https://api.tariffs.ekz.ch/swagger
def fetch_prices(config: EkzTariffConfiguration) -> Dict[str, float]:
    pricelist = readApi()
    prices: Dict[str, float] = dict(pricelist)
    return prices


def create_electricity_tariff(config: EkzTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=EkzTariff)
