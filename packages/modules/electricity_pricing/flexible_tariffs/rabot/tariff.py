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
    # Ohne Zeitraum liefert der Proxy isSuccess=true mit 0 Einträgen (consideredDataPeriod: null), siehe #3883 --
    # Name/Format dieser Parameter ist nicht dokumentiert und an einem echten Rabot-Konto zu verifizieren.
    now = datetime.datetime.now()
    params = {
        "startDate": now.strftime("%Y-%m-%d"),
        "endDate": (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    }
    url = (
        f"https://rabot.openwb.de/rabot-proxy.php/customers/{config.configuration.customer_number}"
        f"/contracts/{config.configuration.contract_number}/metrics"
    )
    response_data = req.get_http_session().get(url, params=params, timeout=15).json()["data"]
    raw_prices = response_data["records"]
    if len(raw_prices) == 0:
        raise Exception("Es konnten keine Preise vom Rabot-Server abgerufen werden. Bitte prüfe, ob dein Konto mit"
                        f" einem dynamischen Stromvertrag verknüpft ist. "
                        f"(Zeitraum: {params}, Antwort: {response_data})")
    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["value"] / 100000  # ct/kWh -> €/Wh
        timestamp = datetime.datetime.strptime(data["moment"], "%Y-%m-%d %H:%M").timestamp()
        prices.update({str(int(timestamp)): formatted_price})
    return prices


def create_electricity_tariff(config: RabotTariff):
    def updater():
        return TariffState(prices=fetch(config))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=RabotTariff)
