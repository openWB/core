#!/usr/bin/env python3
import datetime
import logging
from typing import Dict
import pytz

from dataclass_utils import asdict
from helpermodules import timecheck
from helpermodules.pub import Pub
from modules.common import configurable_tariff, req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.voltego.config import VoltegoTariff, VoltegoToken

log = logging.getLogger(__name__)


def validate_token(config: VoltegoTariff) -> None:
    if config.configuration.token.expires_in:
        expiration = config.configuration.token.created_at + config.configuration.token.expires_in
        log.debug("No need to authenticate. Valid token already present.")
        if timecheck.create_timestamp() > expiration:
            log.debug("Access token expired. Refreshing token.")
            _refresh_token(config)
    else:
        _refresh_token(config)


def _refresh_token(config: VoltegoTariff):
    response = req.get_http_session().post(
        "https://api.voltego.de/oauth/token",
        data={"grant_type": "client_credentials", "scope": 'market_data:read'},
        auth=(config.configuration.client_id, config.configuration.client_secret),
    ).json()
    config.configuration.token = VoltegoToken(access_token=response["access_token"],
                                              expires_in=response["expires_in"],
                                              created_at=timecheck.create_timestamp())
    Pub().pub("openWB/set/optional/et/provider", asdict(config))


def fetch(config: VoltegoTariff) -> None:
    validate_token(config)
    # start_date von voller Stunde sonst liefert die API die nächste Stunde
    start_date = datetime.datetime.fromtimestamp(
        timecheck.create_unix_timestamp_current_full_hour()).astimezone(
            pytz.timezone("Europe/Berlin")).isoformat(sep="T", timespec="seconds")
    if datetime.datetime.today().astimezone(pytz.timezone("Europe/Berlin")).dst().total_seconds()/3600:
        # Sommerzeit
        timezone = "UTC+2:00"
    else:
        timezone = "UTC+1:00"
    raw_prices = req.get_http_session().get(
        "https://api.voltego.de/market_data/day_ahead/DE_LU/60",
        headers={"Content-Type": "application/json;charset=UTF-8",
                 "Authorization": f'Bearer {config.configuration.token.access_token}'},
        params={"from": start_date, "tz": timezone}
    ).json()["elements"]
    prices: Dict[int, float] = {}
    for data in raw_prices:
        formatted_price = data["price"]/1000000  # €/MWh -> €/Wh
        timestamp = datetime.datetime.fromisoformat(data["begin"]).astimezone(
            pytz.timezone("Europe/Berlin")).timestamp()
        prices.update({int(timestamp): formatted_price})
    return prices


def create_electricity_tariff(config: VoltegoTariff):
    validate_token(config)

    def updater():
        return TariffState(prices=fetch(config))
    return configurable_tariff.ConfigurableElectricityTariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=VoltegoTariff)
