#!/usr/bin/env python3
from typing import Dict, Callable
from helpermodules import timecheck
import json

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common import req
from modules.electricity_tariffs.tibber.config import TibberTariffConfiguration
from modules.electricity_tariffs.tibber.config import TibberTariff
import logging
import datetime


# Demo-Token: 5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE
# Demo Home-ID: 96a14971-525a-4420-aae9-e5aedaa129ff

AS_EURO_PER_Wh = 1000
log = logging.getLogger(__name__)


def _get_sorted_price_data(response_json: Dict, key: str):
    return sorted(response_json['data']['viewer']['home']['currentSubscription']
                  ['priceInfo'][key], key=lambda k: (k['startsAt'], k['total']))


def fetch_prices(config: TibberTariffConfiguration) -> Dict[str, float]:
    headers = {'Authorization': 'Bearer ' + config.token, 'Content-Type': 'application/json'}
    query = """
    query PriceInfo($homeId: ID!) {
      viewer {
        home(id: $homeId) {
          currentSubscription {
            priceInfo(resolution: QUARTER_HOURLY) {
              today { total startsAt }
              tomorrow { total startsAt }
            }
          }
        }
      }
    }
    """

    payload = {
        "query": query,
        "variables": {"homeId": config.home_id},
    }
    data = json.dumps(payload)
    response = req.get_http_session().post('https://api.tibber.com/v1-beta/gql', headers=headers, data=data, timeout=6)
    response_json = response.json()
    if response_json.get("errors") is None:
        today_prices = _get_sorted_price_data(response_json, 'today')
        tomorrow_prices = _get_sorted_price_data(response_json, 'tomorrow')
        sorted_market_prices = today_prices + tomorrow_prices
        current_hour = timecheck.create_unix_timestamp_current_quarter_hour()
        log.debug(f"current full hour: {int(current_hour)} "
                  f"{datetime.datetime.fromtimestamp(int(current_hour)).strftime('%Y-%m-%d %H:%M')} ")
        return {
            str(timecheck.convert_to_timestamp(timeslot['startsAt'])): float(timeslot['total']) / AS_EURO_PER_Wh
            for timeslot in sorted_market_prices
            if timecheck.convert_to_timestamp(timeslot['startsAt']) >= int(current_hour)  # is current timeslot or futur
            }
    else:
        error = response_json['errors'][0]['message']
        raise Exception(error)


def create_electricity_tariff(config: TibberTariff) -> Callable[[], TariffState]:
    def updater():
        return TariffState(prices=fetch_prices(config.configuration), prices_per_hour=4)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=TibberTariff)
