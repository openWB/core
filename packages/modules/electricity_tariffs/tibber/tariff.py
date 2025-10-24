#!/usr/bin/env python3
from typing import Callable
from helpermodules import timecheck
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common import req
from modules.electricity_tariffs.tibber.config import TibberTariffConfiguration
from modules.electricity_tariffs.tibber.config import TibberTariff
import json


# Demo-Token: 5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE
# Demo Home-ID: 96a14971-525a-4420-aae9-e5aedaa129ff

AS_EURO_PER_Wh = 1000


def _get_sorted_price_data(response_json: dict, day: str) -> dict[str, float]:
    prices = sorted(response_json['data']['viewer']['home']['currentSubscription']
                    ['priceInfo'][day], key=lambda k: (k['startsAt'], k['total']))
    return {str(timecheck.convert_to_timestamp(price['startsAt'])):  # timestamp
            float(price['total']) / AS_EURO_PER_Wh                   # prices
            for price in prices}


def fetch_prices(config: TibberTariffConfiguration) -> dict[str, float]:
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
        sorted_market_prices = {**today_prices, **tomorrow_prices}
        return sorted_market_prices
    else:
        error = response_json['errors'][0]['message']
        raise Exception(error)


def create_electricity_tariff(config: TibberTariff) -> Callable[[], TariffState]:
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=TibberTariff)
