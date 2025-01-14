#!/usr/bin/env python3
import datetime
import logging
from typing import Dict
from requests.exceptions import HTTPError

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    import pytz

from dataclass_utils import asdict
from helpermodules import timecheck
from helpermodules.pub import Pub
from modules.common import configurable_tariff, req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.rabot.config import RabotTariff, RabotToken

log = logging.getLogger(__name__)


def validate_token(config: RabotTariff) -> None:
    if config.configuration.token.expires_in:
        expiration = config.configuration.token.created_at + config.configuration.token.expires_in
        log.debug("No need to authenticate. Valid token already present.")
        if timecheck.create_timestamp() > expiration:
            log.debug("Access token expired. Refreshing token.")
            _refresh_token(config)
    else:
        _refresh_token(config)


def _refresh_token(config: RabotTariff):
    data = {
        'client_id': {config.configuration.client_id},
        'client_secret': {config.configuration.client_secret},
        'grant_type': 'client_credentials',
        'scope': 'openid offline_access api:hems',
    }
    response = req.get_http_session().post(
        'https://test-auth.rabot-charge.de/connect/token?client_id=&client_secret=&username=&password=&scope=*&'
        + 'grant_type=client_credentials', data=data).json()
    config.configuration.token = RabotToken(access_token=response["access_token"],
                                            expires_in=response["expires_in"],
                                            created_at=timecheck.create_timestamp())
    Pub().pub("openWB/set/optional/et/provider", asdict(config))


def fetch(config: RabotTariff) -> None:
    def get_raw_prices():
        return req.get_http_session().get(
            "https://test-api.rabot-charge.de/hems/v1/day-ahead-prices/limited",
            headers={"Content-Type": "application/json",
                     "Authorization": f'Bearer {config.configuration.token.access_token}'},
            params={"from": start_date, "tz": timezone}
        ).json()["records"]

    validate_token(config)
    # ToDo: get rid of hard coded timezone!
    # start_date von voller Stunde sonst liefert die API die nächste Stunde
    start_date = datetime.datetime.fromtimestamp(
        timecheck.create_unix_timestamp_current_full_hour()).astimezone(
            pytz.timezone("Europe/Berlin")).isoformat(sep="T", timespec="seconds")
    if datetime.datetime.today().astimezone(pytz.timezone("Europe/Berlin")).dst().total_seconds()/3600:
        # Sommerzeit
        timezone = "UTC+2:00"
    else:
        timezone = "UTC+1:00"
    try:
        raw_prices = get_raw_prices()
    except HTTPError as error:
        if error.response.status_code == 401:
            _refresh_token(config)
            raw_prices = get_raw_prices()
        else:
            raise error
    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["priceInCentPerKwh"]/100000  # Cent/kWh -> €/Wh
        timestamp = datetime.datetime.fromisoformat(data["timestamp"]).astimezone(
            pytz.timezone("Europe/Berlin")).timestamp()
        prices.update({str(int(timestamp)): formatted_price})
    return prices


def create_electricity_tariff(config: RabotTariff):
    validate_token(config)

    def updater():
        return TariffState(prices=fetch(config))
    return configurable_tariff.ConfigurableElectricityTariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=RabotTariff)
