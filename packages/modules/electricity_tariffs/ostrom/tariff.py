#!/usr/bin/env python3
import logging
from base64 import b64encode
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from typing import Dict
from requests.exceptions import HTTPError
from helpermodules import timecheck
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_tariffs.ostrom.config import OstromTariffConfiguration
from modules.electricity_tariffs.ostrom.config import OstromTariff, OstromToken

log = logging.getLogger(__name__)


def validate_token(config: OstromTariffConfiguration) -> None:
    if config.token.expires_in:
        expiration = config.token.created_at + config.token.expires_in
        log.debug("No need to authenticate. Valid token already present.")
        if timecheck.create_timestamp() > expiration:
            log.debug("Access token expired. Refreshing token.")
            _refresh_token(config)
    else:
        _refresh_token(config)


def _refresh_token(config: OstromTariffConfiguration):
    response = req.get_http_session().post(
        url="https://auth.production.ostrom-api.io/oauth2/token",
        data={"grant_type": "client_credentials"},
        headers={
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "authorization": "Basic " + b64encode((config.client_id + ":" + config.client_secret).encode()).decode()
        }
    ).json()
    config.token = OstromToken(access_token=response["access_token"],
                               expires_in=response["expires_in"],
                               created_at=timecheck.create_timestamp())


def fetch_prices(config: OstromTariffConfiguration) -> Dict[int, float]:
    def get_raw_prices():
        return req.get_http_session().get(
            url="https://production.ostrom-api.io/spot-prices?" +
                f"startDate={startDate}&endDate={endDate}&resolution=HOUR{zip}",
            headers={
                "accept": "application/json",
                "authorization": "Bearer " + config.token.access_token
            }
        ).json()["data"]

    validate_token(config)
    utcnow = datetime.now(timezone.utc)
    startDate = quote(utcnow.strftime("%Y-%m-%dT%H:00:00.000Z"))
    endDate = quote((utcnow + timedelta(days=1)).strftime("%Y-%m-%dT%H:00:00.000Z"))
    if config.zip:
        zip = f"&zip={config.zip}"
    else:
        zip = ""
    try:
        raw_prices = get_raw_prices()
    except HTTPError as error:
        if error.response.status_code == 401:
            _refresh_token(config)
            raw_prices = get_raw_prices()
        else:
            raise error
    prices: Dict[int, float] = {}
    for raw_price in raw_prices:
        # Note: with Python >= 3.11, we can use: timestamp = datetime.fromisoformat(raw_price["date"]).timestamp()
        timestamp = datetime.strptime(raw_price["date"], "%Y-%m-%dT%H:%M:%S.000Z")\
            .replace(tzinfo=timezone.utc).timestamp()
        price = float(raw_price["grossKwhPrice"] + raw_price["grossKwhTaxAndLevies"]) / 100000  # ct/kWh --> EUR/Wh
        prices.update({str(int(timestamp)): price})
    return prices


def create_electricity_tariff(config: OstromTariff):
    def updater():
        return TariffState(prices=fetch_prices(config.configuration))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=OstromTariff)
