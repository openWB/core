#!/usr/bin/env python3
from datetime import datetime, timezone
from typing import Dict
from helpermodules import timecheck

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableElectricityTariff
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
        sorted_marketprices = today_prices + tomorrow_prices
        prices: Dict[int, float] = {}
        i = 0
        for price_data in sorted_marketprices:
            # konvertiere Time-String (Format 2021-02-06T00:00:00+01:00) ()':' nicht von strptime unterstützt)
            time_str = ''.join(price_data['startsAt'].rsplit(':', 1))
            startzeit_localized = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            starttime_utc = int(startzeit_localized.astimezone(timezone.utc).timestamp())
            if timecheck.create_unix_timestamp_current_full_hour() <= starttime_utc:
                if i < 24:
                    prices.update({starttime_utc: price_data['total'] / 1000})
                    i += 1
                else:
                    break
    else:
        error = response_json['errors'][0]['message']
        raise Exception(error)
    return prices


def create_electricity_tariff(config: TibberTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return ConfigurableElectricityTariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=TibberTariff)
