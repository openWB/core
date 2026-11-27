#!/usr/bin/env python3
from typing import Callable

from helpermodules import timecheck
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common.tariff_errors import PermanentTariffError
from modules.electricity_pricing.flexible_tariffs.ews_schoenau.config import EwsSchoenauTariff
from modules.electricity_pricing.flexible_tariffs.ews_schoenau.config import EwsSchoenauTariffConfiguration

URL = "https://api.ews-schoenau.de/v1/dynamicprices/EWS-OEKO-DYN"
CT_PER_KWH_TO_EURO_PER_WH = 100000


def fetch_prices(config: EwsSchoenauTariffConfiguration) -> dict[str, float]:
    if not config.api_key:
        raise PermanentTariffError("Es ist kein API-Key konfiguriert.")
    response = req.get_http_session().get(URL, headers={"X-API-Key": config.api_key}, timeout=(2, 10)).json()
    prices = {str(timecheck.convert_to_timestamp(entry["startsAt"])): entry["total"] / CT_PER_KWH_TO_EURO_PER_WH
              for entry in (response.get("today") or []) + (response.get("tomorrow") or [])}
    if not prices:
        raise ValueError("Die EWS Schönau API hat keine Preise geliefert.")
    return prices


def create_electricity_tariff(config: EwsSchoenauTariff) -> Callable[[], TariffState]:
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=EwsSchoenauTariff)
