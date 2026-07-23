#!/usr/bin/env python3
import datetime
import pytz
import logging
from typing import Dict
from requests.exceptions import HTTPError
from dataclass_utils import asdict

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.flexible_tariffs.naturstrom.config import NaturstromTariff, NaturstromToken

from helpermodules import timecheck
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


def _get_raw_prices(config: NaturstromTariff):
    headers = {
        'Accept': 'application/json',
        'Authorization': f"{config.configuration.token.token_type or 'Bearer'} {config.configuration.token.access_token}"
    }
    now = datetime.datetime.now(pytz.timezone("Europe/Berlin"))
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = start_of_today + datetime.timedelta(days=1) - datetime.timedelta(minutes=1)

    params = {
        # Hier dann nochmal fragen, ob wir die Daten für den aktuellen Tag passen
        'start': start_of_today.isoformat(),
        'stop': end_of_today.isoformat(),
    }
    return req.get_http_session().get(
        f"https://naturstrom-staging.powerquartier.de/api/public/accounts/{config.configuration.account_id}/rate",
        headers=headers,
        params=params
    ).json()


def validate_token(config: NaturstromTariff) -> None:
    """Prüft ob ein gültiger Token vorhanden ist, ansonsten wird ein neuer abgerufen."""
    if (config.configuration.token.access_token is not None):
        # Access Token vorhanden
        if (config.configuration.token.expires and config.configuration.token.created_at):
            # Prüfe ob Token noch gültig ist
            expires_timestamp = config.configuration.token.created_at + config.configuration.token.expires - 300
            current_timestamp = timecheck.create_timestamp()

            if current_timestamp < expires_timestamp:
                log.debug("Access Token ist noch gültig.")
                return
    # Kein gültiger Token vorhanden oder abgelaufen, versuche Refresh Token
    if config.configuration.token.refresh_token:
        # Refresh Token vorhanden, versuche Access Token zu erneuern
        log.debug("Access Token ist abgelaufen. Versuche Refresh Token.")
        _refresh_token(config)
    else:
        # Kein Refresh Token vorhanden. Authentifizierung erforderlich.
        raise Exception(
            "Refresh Token ist nicht vorhanden. Bitte authentifizieren Sie sich erneut.")


def _refresh_token(config: NaturstromTariff) -> None:
    """Erneuert den Access Token mit dem Refresh Token."""
    if not config.configuration.token.refresh_token:
        raise Exception(
            "Access Token ist abgelaufen und kein Refresh Token vorhanden. Bitte authentifizieren Sie sich erneut.")

    log.debug("Versuche Access Token mit Refresh Token zu erneuern.")
    data = {
        'grant_type': 'refresh_token',
        'client_id': 'exnaton-public',
        'refresh_token': config.configuration.token.refresh_token
    }
    try:
        token_data = req.get_http_session().post(
            'https://naturstrom-staging.powerquartier.de/api/public-auth/oauth2/token',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ).json()
        config.configuration.token = NaturstromToken(
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires=token_data.get("expires_in"),
            created_at=timecheck.create_timestamp()
        )
        Pub().pub("openWB/set/optional/ep/flexible_tariff/provider", asdict(config))
        log.debug("Token erfolgreich erneuert.")
    except HTTPError as e:
        raise Exception(f"Token-Erneuerung fehlgeschlagen: {e}.") from e


def fetch(config: NaturstromTariff) -> Dict[str, float]:
    validate_token(config)
    try:
        raw_prices = _get_raw_prices(config)
    except HTTPError as error:
        raise error

    prices: Dict[str, float] = {}
    for data in raw_prices["data"]:
        formatted_price = data["price"] / 1000  # €/kWh -> €/Wh
        timestamp = int(datetime.datetime.fromisoformat(data["start_time"].replace("Z", "+00:00")).timestamp())
        prices[str(timestamp)] = formatted_price
    return prices


def create_electricity_tariff(config: NaturstromTariff):
    def updater():
        return TariffState(prices=fetch(config))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=NaturstromTariff)
