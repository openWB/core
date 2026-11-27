#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
from dateutil import tz
from urllib.parse import quote
from typing import Dict
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.flexible_tariffs.groupe_e.config import GroupeETariffConfiguration
from modules.electricity_pricing.flexible_tariffs.groupe_e.config import GroupeETariff


# Extract timestamp from power price entry
def timestamp(power):
    return str(int(datetime.strptime(power['start_timestamp'], "%Y-%m-%dT%H:%M:%S%z")
                   .astimezone(tz.tzutc()).timestamp()))


# Read prices from Groupe E API (v2, v1 wurde abgeschaltet)
def readApi() -> list[tuple[str, float]]:
    endpoint = "https://api.tariffs.groupe-e.ch/v2/tariffs"
    utcnow = datetime.now(timezone.utc)
    startDate = utcnow.strftime("%Y-%m-%dT%H:00:00Z")
    endDate = (utcnow + timedelta(days=2)).strftime("%Y-%m-%dT%H:00:00Z")
    prices_raw = req.get_http_session().get(
        url=endpoint +
        f"?start_timestamp={quote(startDate)}&end_timestamp={quote(endDate)}",
    ).json()["prices"]
    return [(timestamp(price), integrated_price(price) / 1000) for price in prices_raw]  # CHF/kWh -> CHF/Wh


def integrated_price(price) -> float:
    return next(entry["value"] for entry in price["integrated"] if entry["unit"] == "CHF_kWh")


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
