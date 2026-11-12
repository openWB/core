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
                  unitRateForecast {
                    validFrom
                    validTo
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
        for rule in rate_info['timeslotActivationRules']:
            active_from = datetime.strptime(rule['activeFromTime'], '%H:%M:%S').time()
            active_to = datetime.strptime(rule['activeToTime'], '%H:%M:%S').time()
            if active_from == active_to:
                in_slot = True
            elif active_from < active_to:
                in_slot = active_from <= local_hour_time < active_to
            else:
                # Mitternachts-Überlauf
                in_slot = local_hour_time >= active_from or local_hour_time < active_to

            if in_slot:
                return float(rate_info['latestGrossUnitRateCentsPerKwh']) / 100 / 1000
    return None


def get_rate_from_unit_rate_info(unit_rate_info: dict, hour_time_utc: datetime) -> Optional[float]:
    if unit_rate_info['__typename'] == 'SimpleProductUnitRateInformation':
        return get_rate_from_simple_product(unit_rate_info)
    elif unit_rate_info['__typename'] == 'TimeOfUseProductUnitRateInformation':
        return get_rate_from_time_of_use_product(unit_rate_info, hour_time_utc)
    return None


def agreement_active_at(agreement: dict, time_utc: datetime) -> bool:
    if agreement['validTo'] is None:
        return True
    valid_from = parse_datetime(agreement['validFrom'])
    valid_to = parse_datetime(agreement['validTo'])
    return valid_from <= time_utc <= valid_to


def process_agreement(agreement: dict, current_utc: datetime, horizon_utc: datetime, prices: Dict[str, float]):
    forecast = agreement.get('unitRateForecast') or []
    forecast_intervals = []
    for entry in forecast:
        valid_from = parse_datetime(entry['validFrom'])
        valid_to = parse_datetime(entry['validTo']) if entry.get('validTo') else horizon_utc
        if valid_to <= current_utc or valid_from >= horizon_utc:
            continue
        forecast_intervals.append((valid_from, valid_to))
        if agreement_active_at(agreement, valid_from):
            rate = get_rate_from_unit_rate_info(entry['unitRateInformation'], valid_from)
            if rate is not None:
                timestamp = str(int(valid_from.astimezone(GERMAN_TZ).timestamp()))
                prices[timestamp] = rate

    # Lücken im Forecast (oder sein komplettes Fehlen) werden mit unitRateInformation aufgefüllt, im selben
    # Takt wie der Forecast - sonst leitet ep_get_loading_hours() aus den ersten beiden Preisen eine falsche,
    # global geltende Slot-Länge ab.
    if forecast_intervals:
        step = forecast_intervals[0][1] - forecast_intervals[0][0]
        round_to_hour = False
    else:
        step = timedelta(hours=1)
        round_to_hour = True

    offset = timedelta()
    while current_utc + offset < horizon_utc:
        time_utc = current_utc + offset
        if (not any(start <= time_utc < end for start, end in forecast_intervals)
                and agreement_active_at(agreement, time_utc)):
            rate = get_rate_from_unit_rate_info(agreement['unitRateInformation'], time_utc)
            if rate is not None:
                local_time = time_utc.astimezone(GERMAN_TZ)
                if round_to_hour:
                    local_time = local_time.replace(minute=0, second=0, microsecond=0)
                prices[str(int(local_time.timestamp()))] = rate
        offset += step


def build_tariff_state(data: dict) -> Dict[str, float]:
    current_utc = datetime.now(timezone.utc)
    horizon_utc = current_utc + timedelta(hours=28)
    prices: Dict[str, float] = {}

    property_data = data.get('account', {}).get('property')
    if not property_data:
        raise OctopusEnergyApiError("Keine Property-Daten in der Antwort enthalten.")

    malos = property_data.get('electricityMalos')
    if not malos:
        error_message = "Kein electricityMalos-Eintrag in der Antwort enthalten " \
            "(Zählpunkt evtl. noch nicht aktiv/verknüpft)."
        raise OctopusEnergyApiError(error_message)

    for agreement in malos[0]['agreements']:
        process_agreement(agreement, current_utc, horizon_utc, prices)

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
