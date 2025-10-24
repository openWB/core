#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
from dateutil import tz
from urllib.parse import quote
from typing import Dict
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.groupe_e.config import GroupeETariffConfiguration
from modules.electricity_tariffs.groupe_e.config import GroupeETariff


# Combine power and grid prices, convert to kWh
def transformPrices(power: dict) -> tuple[str, float]:
    timestamp = str(int(datetime.strptime(power['start_timestamp'], "%Y-%m-%dT%H:%M:%S%z")
                    .astimezone(tz.tzutc()).timestamp()))
    power_price = power['vario_plus']
    return (timestamp, power_price/100000)


# Read prices from Groupe E API
def readApi() -> list[tuple[str, float]]:
    endpoint = "https://api.tariffs.groupe-e.ch/v1/tariffs"
    utcnow = datetime.now(timezone.utc)
    startDate = quote(utcnow.strftime("%Y-%m-%dT%H:00:00+02:00"))
    endDate = quote((utcnow + timedelta(days=2)).strftime("%Y-%m-%dT%H:00:00+02:00"))
    session = req.get_http_session()
    power_raw = session.get(
        url=endpoint +
        f"?start_timestamp={startDate}&end_timestamp={endDate}",
        ).json()
    return list(map(transformPrices, power_raw))


def fetch_prices(config: GroupeETariffConfiguration) -> Dict[str, float]:
    # Fetch electricity prices from EKZ API
    pricelist = readApi()
    prices: Dict[str, float] = dict(pricelist)
    return prices


def create_electricity_tariff(config: GroupeETariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=GroupeETariff)
