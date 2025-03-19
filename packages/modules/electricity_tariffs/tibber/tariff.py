#!/usr/bin/env python3
from datetime import datetime
from typing import Dict
from helpermodules import timecheck

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common import req
from modules.electricity_tariffs.tibber.config import TibberTariffConfiguration
from modules.electricity_tariffs.tibber.config import TibberTariff


# Demo-Token: 5K4MVS-OjfWhK_4yrjOlFe1F6kJXPVf7eQYggo8ebAE
# Demo Home-ID: 96a14971-525a-4420-aae9-e5aedaa129ff


def _get_sorted_price_data(response_json: Dict, key: str):
    return sorted(response_json['data']['viewer']['home']['currentSubscription']
                  ['priceInfo'][key], key=lambda k: (k['startsAt'], k['total']))


def fetch_prices(config: TibberTariffConfiguration) -> Dict[int, float]:
    headers = {'Authorization': 'Bearer ' + config.token, 'Content-Type': 'application/json'}
    data = '{ "query": "{viewer {home(id:\\"' + config.home_id + \
        '\\") {currentSubscription {priceInfo {today {total startsAt} tomorrow {total startsAt}}}}}}" }'
    response = req.get_http_session().post('https://api.tibber.com/v1-beta/gql', headers=headers, data=data, timeout=6)
    response_json = response.json()
    if response_json.get("errors") is None:
        today_prices = _get_sorted_price_data(response_json, 'today')
        tomorrow_prices = _get_sorted_price_data(response_json, 'tomorrow')
        sorted_market_prices = today_prices + tomorrow_prices
        prices: Dict[int, float] = {}
        current_hour = timecheck.create_unix_timestamp_current_full_hour()
        for price_data in sorted_market_prices:
            start_time_epoch = datetime.fromisoformat(price_data['startsAt']).timestamp()
            if current_hour <= start_time_epoch:
                prices.update({str(int(start_time_epoch)): price_data['total'] / 1000})
    else:
        error = response_json['errors'][0]['message']
        raise Exception(error)
    return prices


def create_electricity_tariff(config: TibberTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=TibberTariff)
