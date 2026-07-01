#!/usr/bin/env python3
import datetime
import logging
from typing import Dict

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.flexible_tariffs.smartEnergy.config import SmartEnergyTariff

log = logging.getLogger(__name__)


def fetch(config: SmartEnergyTariff) -> None:
    raw_prices = req.get_http_session().get(
        f"https://apis.smartenergy.at/market/v1/price",
        timeout=15
    ).json()["data"]
    if len(raw_prices) == 0:
        raise Exception("Es konnten keine Preise vom SmartEnergy-Server abgerufen werden.")
    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["value"] / 100000  # ct/kWh -> €/Wh
        timestamp = datetime.datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
        prices.update({str(int(timestamp)): formatted_price})
    return prices


def create_electricity_tariff(config: SmartEnergyTariff):
    def updater():
        return TariffState(prices=fetch(config))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=SmartEnergyTariff)
