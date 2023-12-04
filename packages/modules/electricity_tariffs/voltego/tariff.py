#!/usr/bin/env python3
import datetime
import logging

import pytz
from helpermodules import timecheck
from helpermodules.pub import Pub

from modules.common import configurable_tariff, req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.voltego.config import VoltegoTariff, VoltegoTariffConfiguration, VoltegoToken

log = logging.getLogger(__name__)


def validate_token(config: VoltegoTariffConfiguration) -> None:
    expiration = config.token.created_at + config.token.expires_in
    log.debug("No need to authenticate. Valid token already present.")
    if timecheck.create_timestamp_unix() > expiration:
        log.debug("Access token expired. Refreshing token.")
        _refresh_token(config)


def _refresh_token(config: VoltegoTariffConfiguration):
    response = req.get_http_session().post(
        "https://api.voltego.de/oauth/token",
        data={"grant_type": "client_credentials", "scope": 'market_data:read'},
        auth=(config.client_id, config.client_secret),
    ).json()
    config.token = VoltegoToken(token=response["access_token"],
                                expires_in=response["expires_in"],
                                created_at=timecheck.create_timestamp_unix())
    Pub().pub("openWB/set/optional/et/provider", config)


def fetch(config: VoltegoTariffConfiguration) -> None:
    if validate_token():
        _refresh_token(config)
    start_date = datetime.datetime.fromtimestamp(
        timecheck.create_unix_timestamp_current_full_hour()).astimezone(pytz.timezone("Europe/Berlin")).isoformat(sep="T", timespec="seconds")
    if datetime.datetime.today().astimezone(pytz.timezone("Europe/Berlin")).dst().total_seconds()/3600:
        timezone = "UTC(+1)"
    else:
        timezone = "UTC"
    response = req.get_http_session().get(
        f"https://api.voltego.de/market_data/day_ahead/DE_LU/60?from={start_date}&tz={timezone}",
        headers={"Content-Type": "application/json;charset=UTF-8",
                 "Authorization": f'Bearer {config.token.token}'},
        params={"from": "2023-12-04T08:00:00+00:00", "tz": "UTC+1:00"}
    ).json()
# /1000000  # €/MWh -> €/Wh
    return TariffState(prices=response["price_list"])


def create_electricity_tariff(config: VoltegoTariff):
    if config.configuration.token.expires_in:
        if validate_token():
            _refresh_token(config.configuration)
    else:
        _refresh_token(config.configuration)

    def updater():
        return fetch(config.configuration)
    return configurable_tariff(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=VoltegoTariff)
