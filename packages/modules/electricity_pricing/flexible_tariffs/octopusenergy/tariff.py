#!/usr/bin/env python3
import logging
import pytz
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from modules.electricity_pricing.flexible_tariffs.octopusenergy.config import (OctopusEnergyTariffConfiguration,
                                                                               OctopusEnergyTariff)
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState

log = logging.getLogger(__name__)

GERMAN_TZ = pytz.timezone("Europe/Berlin")


class OctopusEnergyApiError(Exception):
    """Wird geworfen, wenn die Kraken-API kein verwertbares 'data'-Feld liefert
    (z.B. GraphQL-Fehler, abgelaufener Token, Wartungsarbeiten bei Octopus)."""
    pass


class OctopusEnergyClient:
    def __init__(self, email: str, password: str, base_url="https://api.oeg-kraken.energy/v1/graphql/"):
        self.base_url = base_url
        self.token = None
        self.session = req.get_http_session()
        self.authenticate(email, password)

    def _graphql_request(self, query: str, variables: dict) -> dict:
        """Sendet einen GraphQL-Request mit Authentifizierung.

        Wirft OctopusEnergyApiError, wenn die Antwort kein 'data'-Feld enthält
        (statt stillschweigend None zurückzugeben und den Fehler an den Aufrufer
        weiterzureichen, wo er als kryptischer NoneType-Fehler auftaucht).
        """
        headers = {
            "Authorization": f"{self.token}" if self.token else "",
            "Content-Type": "application/json"
        }
        payload = {"query": query, "variables": variables}

        response = self.session.post(self.base_url, json=payload, headers=headers)

        if response.status_code != 200:
            raise OctopusEnergyApiError(f"API request failed: {response.text}")

        body = response.json()

        # GraphQL-APIs liefern bei fachlichen Fehlern trotzdem HTTP 200,
        # aber ein "errors"-Array statt (oder zusätzlich zu) "data".
        if body.get("errors"):
            error_messages = "; ".join(
                err.get("message", str(err)) for err in body["errors"]
            )
            raise OctopusEnergyApiError(f"GraphQL-Fehler: {error_messages}")

        data = body.get("data")
        if data is None:
            raise OctopusEnergyApiError("Antwort enthält kein 'data'-Feld: " + str(body)[:500])

        return data

    def authenticate(self, email: str, password: str):
        """Authentifiziert und speichert den Token."""
        mutation = """
        mutation krakenTokenAuthentication($email: String!, $password: String!) {
          obtainKrakenToken(input: {email: $email, password: $password}) {
            token
          }
        }
        """
        variables = {"email": email, "password": password}
        data = self._graphql_request(mutation, variables)

        if "obtainKrakenToken" not in data or data["obtainKrakenToken"] is None:
            raise OctopusEnergyApiError("Authentifizierung fehlgeschlagen: Kein Token in der Antwort enthalten.")

        self.token = data["obtainKrakenToken"]["token"]

    def get_property_ids(self, account_number: str) -> dict:
        """Ruft die Property-IDs für einen Account ab."""
        query = """
        query getPropertyIds($accountNumber: String!) {
          account(accountNumber: $accountNumber) {
            properties {
              id
              occupancyPeriods {
                effectiveFrom
                effectiveTo
              }
            }
          }
        }
        """
        variables = {"accountNumber": account_number}
        return self._graphql_request(query, variables)

    def get_smart_meter_usage(self, account_number: str, property_id: str) -> dict:
        """Ruft Tarif- und Verbrauchsinformationen für eine Property ab."""
        query = """
        query getSmartMeterUsage($accountNumber: String!, $propertyId: ID!) {
          account(accountNumber: $accountNumber) {
            property(id: $propertyId) {
              electricityMalos {
                agreements {
                  id
                  unitRateInformation {
                    ... on SimpleProductUnitRateInformation {
                      __typename
                      latestGrossUnitRateCentsPerKwh
                    }
                    ... on TimeOfUseProductUnitRateInformation {
                      __typename
                      rates {
                        latestGrossUnitRateCentsPerKwh
                        timeslotName
                        timeslotActivationRules {
                          activeFromTime
                          activeToTime
                        }
                      }
                    }
                  }
                  validFrom
                  validTo
                }
              }
            }
          }
        }
        """
        variables = {"accountNumber": account_number, "propertyId": property_id}
        return self._graphql_request(query, variables)


def parse_datetime(datetime_str: str) -> datetime:
    return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))


def get_rate_from_simple_product(unit_rate_info: dict) -> float:
    return float(unit_rate_info['latestGrossUnitRateCentsPerKwh']) / 100 / 1000


def get_rate_from_time_of_use_product(unit_rate_info: dict, hour_time_utc: datetime) -> Optional[float]:
    local_hour_time = hour_time_utc.astimezone(GERMAN_TZ).time()  # hour_time is UTC, time of use returns local time

    for rate_info in unit_rate_info['rates']:
        active_from = datetime.strptime(rate_info['timeslotActivationRules'][0]['activeFromTime'], '%H:%M:%S').time()
        active_to = datetime.strptime(rate_info['timeslotActivationRules'][0]['activeToTime'], '%H:%M:%S').time()
        # Mitternachts-Überlauf korrekt behandeln
        if active_from <= active_to:
            in_slot = active_from <= local_hour_time < active_to
        else:
            in_slot = local_hour_time >= active_from or local_hour_time < active_to

        if in_slot:
            return float(rate_info['latestGrossUnitRateCentsPerKwh']) / 100 / 1000
    return None


def process_agreement(agreement: dict, hour_time_utc: datetime, prices: Dict[str, float]):
    if agreement['validTo'] is None:
        valid = True
    else:
        valid_from = parse_datetime(agreement['validFrom'])
        valid_to = parse_datetime(agreement['validTo'])
        valid = valid_from <= hour_time_utc <= valid_to

    if valid:
        unit_rate_info = agreement['unitRateInformation']
        local_hour_time = hour_time_utc.astimezone(GERMAN_TZ)
        timestamp = str(int(local_hour_time.replace(minute=0, second=0, microsecond=0).timestamp()))
        if unit_rate_info['__typename'] == 'SimpleProductUnitRateInformation':
            prices[timestamp] = get_rate_from_simple_product(unit_rate_info)
        elif unit_rate_info['__typename'] == 'TimeOfUseProductUnitRateInformation':
            rate = get_rate_from_time_of_use_product(unit_rate_info, hour_time_utc)
            if rate is not None:
                log.debug(f"Adding rate: {rate} for timestamp: {timestamp} with hour_time_utc: {hour_time_utc}")
                prices[timestamp] = rate


def build_tariff_state(data: dict) -> Dict[str, float]:
    current_utc = datetime.now(timezone.utc)
    prices: Dict[str, float] = {}

    property_data = data.get('account', {}).get('property')
    if not property_data:
        raise OctopusEnergyApiError("Keine Property-Daten in der Antwort enthalten.")

    malos = property_data.get('electricityMalos')
    if not malos:
        raise OctopusEnergyApiError("Kein electricityMalos-Eintrag in der Antwort enthalten "
                                     "(Zählpunkt evtl. noch nicht aktiv/verknüpft).")

    for hour in range(28):
        hour_time_utc = current_utc + timedelta(hours=hour)
        for agreement in malos[0]['agreements']:
            process_agreement(agreement, hour_time_utc, prices)

    sorted_prices = dict(sorted(prices.items()))
    return sorted_prices


def fetch(config: OctopusEnergyTariffConfiguration) -> TariffState:
    client = OctopusEnergyClient(email=config.email, password=config.password)

    property_data = client.get_property_ids(config.accountId)
    properties = property_data.get('account', {}).get('properties')
    if not properties:
        raise OctopusEnergyApiError(f"Kein Property zum Account {config.accountId} gefunden.")
    property_id = properties[0]['id']

    tariffs = client.get_smart_meter_usage(config.accountId, property_id)
    prices = build_tariff_state(tariffs)

    return TariffState(prices=prices)


def create_electricity_tariff(config: OctopusEnergyTariff) -> callable:
    def updater():
        return fetch(config.configuration)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=OctopusEnergyTariff)
