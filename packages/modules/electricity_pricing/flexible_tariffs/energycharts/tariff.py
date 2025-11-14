import logging
import random
import requests
import time
from typing import Dict
from datetime import datetime, timedelta
from helpermodules import timecheck
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.flexible_tariffs.energycharts.config import EnergyChartsTariffConfiguration
from modules.electricity_pricing.flexible_tariffs.energycharts.config import EnergyChartsTariff

MAX_RETRIES = 10
MAX_DELAY = 10
log = logging.getLogger(__name__)


def get_tomorrow_last_hour_timestamp() -> int:
    tomorrow = datetime.now() + timedelta(days=2)
    return int(tomorrow.timestamp())


def create_request_url(config: EnergyChartsTariffConfiguration) -> str:
    start_time = timecheck.create_unix_timestamp_current_full_hour()
    end_time = get_tomorrow_last_hour_timestamp()
    url = f'https://api.energy-charts.info/price?bzn={config.country}&start={start_time}&end={end_time}'
    log.debug("fetching tariffs: %s", url)
    return url


def parse_response(config: EnergyChartsTariffConfiguration, raw_prices: dict) -> Dict[str, float]:
    prices: Dict[int, float] = {}
    for timestamp, price_per_MWh in zip(raw_prices['unix_seconds'],  raw_prices['price']):
        prices[str(int(timestamp))] = float(price_per_MWh + (config.surcharge*10))/1000000
    log.debug("converted prices: %s : %s", len(prices), prices)
    return prices


def fetch_prices(config: EnergyChartsTariffConfiguration) -> Dict[str, float]:
    url = create_request_url(config)
    for attempt in range(MAX_RETRIES):
        attempt += 1  # one-based indexing
        try:
            response = req.get_http_session().get(url, timeout=(10, 20))
            response.raise_for_status()
            return parse_response(config, response.json())
        except requests.exceptions.Timeout as e:
            if MAX_RETRIES > attempt:
                delay = (attempt) * random.uniform(attempt, MAX_DELAY)
                log.warning(f"Timeout beim Abrufen der Preise (Versuch {attempt}/{MAX_RETRIES}) : {str(e)}"
                            f", neuer Versuch in {delay:.1f} Sekunden...")
                time.sleep(delay)
    raise Exception("Timeout beim Abrufen der Preise nach {MAX_RETRIES} Versuchen")


def create_electricity_tariff(config: EnergyChartsTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=EnergyChartsTariff)
