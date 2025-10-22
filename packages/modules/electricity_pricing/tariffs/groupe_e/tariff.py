#!/usr/bin/env python3
from datetime import datetime, timedelta
from dateutil import tz
from urllib.parse import quote
from typing import Dict
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.tariffs.groupe_e.config import GroupeETariffConfiguration
from modules.electricity_pricing.tariffs.groupe_e.config import GroupeETariff


# Extract timestamp from power price entry
def timestamp(power):
    return str(int(datetime.strptime(power['start_timestamp'], "%Y-%m-%dT%H:%M:%S%z")
                   .astimezone(tz.tzutc()).timestamp()))


# Read prices from Groupe E API
def readApi() -> list[tuple[str, float]]:
    endpoint = "https://api.tariffs.groupe-e.ch/v1/tariffs"
    tariffName = "vario_plus"
    startDate = datetime.now().strftime("%Y-%m-%dT%H:00:00+01:00")
    endDate = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:00:00+01:00")
    session = req.get_http_session()
    prices_raw = session.get(
        url=endpoint +
        f"?start_timestamp={ quote(startDate) }&end_timestamp={ quote(endDate) }",
    ).json()
    return [(timestamp(power), (power[tariffName]/100000))
            for power in prices_raw]


# Fetch prices and return as a dictionary
def fetch_prices(config: GroupeETariffConfiguration) -> Dict[str, float]:
    pricelist = readApi()
    prices: Dict[str, float] = dict(pricelist)
    return prices


def create_electricity_tariff(config: GroupeETariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=GroupeETariff)
