#!/usr/bin/env python3
import datetime
import logging
from typing import Dict
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

    try:
        response = req.get_http_session().post(
            'https://api.wws.tarifdynamik.de/public/tokens',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        token_data = response.json()

        config.configuration.token = WestfalenWindToken(
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires=token_data.get("expires"),
            created_at=timecheck.create_timestamp()
        )

        # Konfiguration speichern
        Pub().pub("openWB/set/optional/ep/flexible_tariff/provider", asdict(config))
        log.debug("Erfolgreich authentifiziert.")

    except HTTPError as e:
        log.error(f"Authentifizierung fehlgeschlagen: {e}")
        raise


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
        response = req.get_http_session().post(
            'https://api.wws.tarifdynamik.de/public/tokens',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        token_data = response.json()

        config.configuration.token = WestfalenWindToken(
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_type=token_data.get("token_type", "Bearer"),
            expires=token_data.get("expires"),
            created_at=timecheck.create_timestamp()
        )

        # Konfiguration speichern
        Pub().pub("openWB/set/optional/ep/flexible_tariff/provider", asdict(config))
        log.debug("Token erfolgreich erneuert.")

    except HTTPError as e:
        log.error(f"Token-Erneuerung fehlgeschlagen: {e}. Führe neue Authentifizierung durch.")
        _authenticate(config)


def fetch(config: WestfalenWindTariff) -> Dict[str, float]:
    """Holt die aktuellen Strompreise von der WestfalenWind API."""

    def get_raw_prices():
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{config.configuration.token.token_type} {config.configuration.token.access_token}"
        }

        params = {}
        if config.configuration.contract_id:
            params['contract_id'] = config.configuration.contract_id

        return req.get_http_session().get(
            "https://api.wws.tarifdynamik.de/public/energyprices/latest",
            headers=headers,
            params=params
        ).json()

    validate_token(config)

    try:
        raw_data = get_raw_prices()
    except HTTPError as error:
        if error.response.status_code == 401:
            log.debug("401 Unauthorized - Token ungültig. Versuche Erneuerung.")
            _authenticate(config)
            raw_data = get_raw_prices()
        else:
            raise error

    prices: Dict[str, float] = {}

    if 'data' in raw_data:
        for price_entry in raw_data['data']:
            # Konvertiere ISO 8601 Zeitstempel zu Unix Timestamp
            start_time = datetime.datetime.fromisoformat(
                price_entry['start'].replace('Z', '+00:00')
            )
            timestamp = int(start_time.timestamp())

            # Konvertiere ct/kWh zu €/Wh
            price_euro_per_wh = price_entry['price_ct_kwh'] / 100000

            prices[str(timestamp)] = price_euro_per_wh

    log.debug(f"WestfalenWind: {len(prices)} Preise abgerufen.")
    return prices


def create_electricity_tariff(config: WestfalenWindTariff):
    """Erstellt den Tariff-Updater für WestfalenWind."""
    validate_token(config)

    def updater():
        return TariffState(prices=fetch(config))

    return updater


device_descriptor = DeviceDescriptor(configuration_factory=WestfalenWindTariff)
