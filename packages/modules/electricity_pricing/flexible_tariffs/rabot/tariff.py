#!/usr/bin/env python3
import datetime
import logging
from typing import Dict

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.flexible_tariffs.rabot.config import RabotTariff

log = logging.getLogger(__name__)


def fetch(config: RabotTariff) -> None:
    raw_prices = req.get_http_session().get(
        f"https://rabot.openwb.de/rabot-proxy.php/customers/{config.configuration.customer_number}"
        f"/contracts/{config.configuration.contract_number}/metrics",
        timeout=15
    ).json()["data"]["records"]
    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["value"]/1000  # €/kWh -> €/Wh
        timestamp = datetime.datetime.strptime(data["moment"], "%Y-%m-%d %H:%M").timestamp()
        prices.update({str(int(timestamp)): formatted_price})
    return prices


def create_electricity_tariff(config: RabotTariff):
    def updater():
        return TariffState(prices=fetch(config))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=RabotTariff)
