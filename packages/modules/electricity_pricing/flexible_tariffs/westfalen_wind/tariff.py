#!/usr/bin/env python3
import datetime
import logging
from typing import Dict
import pytz
from requests.exceptions import HTTPError


from dataclass_utils import asdict
from helpermodules import timecheck
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from modules.electricity_pricing.flexible_tariffs.westfalen_wind.config import WestfalenWindTariff, WestfalenWindToken

log = logging.getLogger(__name__)


def validate_token(config: WestfalenWindTariff) -> None:
    """Prüft ob ein gültiger Token vorhanden ist, ansonsten wird ein neuer abgerufen."""
    if (config.configuration.token.access_token and
        config.configuration.token.expires and
            config.configuration.token.created_at):

        # Prüfe ob Token noch gültig ist (mit 5 Min Puffer)
        expires_timestamp = config.configuration.token.created_at + config.configuration.token.expires - 300
        current_timestamp = timecheck.create_timestamp()

        if current_timestamp < expires_timestamp:
            log.debug("Access Token ist noch gültig.")
            return
        else:
            log.debug("Access Token ist abgelaufen. Versuche Refresh Token.")
            if config.configuration.token.refresh_token:
                _refresh_token(config)
            else:
                _authenticate(config)
    else:
        log.debug("Kein gültiger Token vorhanden. Authentifizierung erforderlich.")
        _authenticate(config)


def _authenticate(config: WestfalenWindTariff) -> None:
    """Authentifizierung mit Benutzername und Passwort."""
    if not config.configuration.username or not config.configuration.password:
        raise ValueError("Benutzername und Passwort sind für die Authentifizierung erforderlich.")

    data = {
        'grant_type': 'password',
        'username': config.configuration.username,
        'password': config.configuration.password
    }
    token_data = req.get_http_session().post(
        'https://api.wws.tarifdynamik.de/public/tokens',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    ).json()

    config.configuration.token = WestfalenWindToken(
        access_token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_type=token_data.get("token_type", "Bearer"),
        expires=token_data.get("expires"),
        created_at=timecheck.create_timestamp()
    )
    Pub().pub("openWB/set/optional/ep/flexible_tariff/provider", asdict(config))
    log.debug("Erfolgreich authentifiziert.")


def _refresh_token(config: WestfalenWindTariff) -> None:
    """Erneuert den Access Token mit dem Refresh Token."""
    if not config.configuration.token.refresh_token:
        log.debug("Kein Refresh Token vorhanden. Führe neue Authentifizierung durch.")
        _authenticate(config)
        return

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': config.configuration.token.refresh_token
    }
    try:
        token_data = req.get_http_session().post(
            'https://api.wws.tarifdynamik.de/public/tokens',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        ).json()
        config.configuration.token = WestfalenWindToken(
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires=token_data.get("expires"),
            created_at=timecheck.create_timestamp()
        )
        Pub().pub("openWB/set/optional/ep/flexible_tariff/provider", asdict(config))
        log.debug("Token erfolgreich erneuert.")
    except HTTPError as e:
        log.error(f"Token-Erneuerung fehlgeschlagen: {e}. Führe neue Authentifizierung durch.")
        _authenticate(config)


def _get_raw_prices(config: WestfalenWindTariff):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{config.configuration.token.token_type} {config.configuration.token.access_token}"
    }
    now = datetime.datetime.now(pytz.timezone("Europe/Berlin"))
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_tomorrow = start_of_today + datetime.timedelta(days=2) - datetime.timedelta(minutes=15)
    filters = [
        f"valid_from:gte:{now.isoformat()}",
        f"valid_from:lte:{end_of_tomorrow.isoformat()}"
    ]
    params = {
        'page_size': 200,  # Maximal 200 Einträge (2 Tage * 96 Viertelstunden)
        'sort': 'valid_from:asc',
        'filters': filters
    }
    if config.configuration.contract_id:
        params['contract_id'] = config.configuration.contract_id

    return req.get_http_session().get(
        "https://api.wws.tarifdynamik.de/public/energyprices",
        headers=headers,
        params=params
    ).json()


def fetch(config: WestfalenWindTariff) -> Dict[str, float]:
    validate_token(config)
    try:
        raw_data = _get_raw_prices(config)
    except HTTPError as error:
        if error.response.status_code == 401:
            log.debug("401 Unauthorized - Token ungültig. Versuche Erneuerung.")
            _authenticate(config)
            raw_data = _get_raw_prices(config)
        else:
            raise error
    prices: Dict[str, float] = {}
    for price_entry in raw_data['data']:
        timestamp = int(datetime.datetime.fromisoformat(price_entry['start'].replace('Z', '+00:00')).timestamp())
        price_euro_per_wh = price_entry['price_ct_kwh'] / 100000
        prices[str(timestamp)] = price_euro_per_wh
    return prices


def create_electricity_tariff(config: WestfalenWindTariff):
    validate_token(config)

    def updater():
        return TariffState(prices=fetch(config))
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=WestfalenWindTariff)
