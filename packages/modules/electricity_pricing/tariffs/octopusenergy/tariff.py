#!/usr/bin/env python3
import logging

from modules.electricity_pricing.tariffs.octopusenergy.config import OctopusEnergyTariffConfiguration, OctopusEnergyTariff
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import TariffState
from typing import Dict
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)


class OctopusEnergyClient:
    def __init__(self, email: str, password: str, base_url="https://api.oeg-kraken.energy/v1/graphql/"):
        self.base_url = base_url
        self.token = None
        self.session = req.get_http_session()
        self.authenticate(email, password)

    def _graphql_request(self, query: str, variables: dict):
        """Send a GraphQL request with authentication."""
        headers = {
            "Authorization": f"{self.token}" if self.token else "",
            "Content-Type": "application/json"
        }
        payload = {"query": query, "variables": variables}

        response = self.session.post(self.base_url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json().get("data")
        else:
            raise Exception(f"API request failed: {response.text}")

    def authenticate(self, email: str, password: str):
        """Authenticate and store the token."""
        mutation = """
        mutation krakenTokenAuthentication($email: String!, $password: String!) {
          obtainKrakenToken(input: {email: $email, password: $password}) {
            token
          }
        }
        """
        variables = {"email": email, "password": password}
        data = self._graphql_request(mutation, variables)

        if data and "obtainKrakenToken" in data:
            self.token = data["obtainKrakenToken"]["token"]
        else:
            raise Exception("Authentication failed")

    def get_property_ids(self, account_number: str):
        """Retrieve property IDs for a given account."""
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

    def get_smart_meter_usage(self, account_number: str, property_id: str):
        """Retrieve tariff and usage information for a property."""
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


def get_rate_from_time_of_use_product(unit_rate_info: dict, hour_time: datetime) -> float:
    for rate_info in unit_rate_info['rates']:
        active_from = datetime.strptime(rate_info['timeslotActivationRules'][0]['activeFromTime'], '%H:%M:%S').time()
        active_to = datetime.strptime(rate_info['timeslotActivationRules'][0]['activeToTime'], '%H:%M:%S').time()
        local_hour_time = hour_time.astimezone().time()  # hour_time is UTC, time of use returns local time
        if active_from <= local_hour_time < active_to or (
           active_to == datetime.min.time() and hour_time.time() >= active_from):
            return float(rate_info['latestGrossUnitRateCentsPerKwh']) / 100 / 1000
    return None


def process_agreement(agreement: dict, hour_time: datetime, prices: Dict[str, float]):
    if agreement['validTo'] is None:
        valid = True
    else:
        valid_from = parse_datetime(agreement['validFrom'])
        valid_to = parse_datetime(agreement['validTo'])
        valid = valid_from <= hour_time <= valid_to

    if valid:
        unit_rate_info = agreement['unitRateInformation']
        timestamp = str(int(hour_time.replace(minute=0, second=0, microsecond=0).timestamp()))
        if unit_rate_info['__typename'] == 'SimpleProductUnitRateInformation':
            prices[timestamp] = get_rate_from_simple_product(unit_rate_info)
        elif unit_rate_info['__typename'] == 'TimeOfUseProductUnitRateInformation':
            rate = get_rate_from_time_of_use_product(unit_rate_info, hour_time)
            if rate is not None:
                log.debug(f"Adding rate: {rate} for timestamp: {timestamp} with hour_time: {hour_time}")
                prices[timestamp] = rate


def build_tariff_state(data) -> Dict[str, float]:
    current_time = datetime.now(timezone.utc)
    prices: Dict[str, float] = {}

    for hour in range(28):
        hour_time = current_time + timedelta(hours=hour)
        for agreement in data['account']['property']['electricityMalos'][0]['agreements']:
            process_agreement(agreement, hour_time, prices)

    sorted_prices = dict(sorted(prices.items()))
    return sorted_prices


def fetch(config: OctopusEnergyTariffConfiguration) -> TariffState:
    client = OctopusEnergyClient(email=config.email, password=config.password)
    property_data = client.get_property_ids(config.accountId)
    property_id = property_data["account"]["properties"][0]["id"]
    tariffs = client.get_smart_meter_usage(config.accountId, property_id)
    prices = build_tariff_state(tariffs)

    return TariffState(prices=prices)


def create_electricity_tariff(config: OctopusEnergyTariff) -> callable:
    def updater():
        return fetch(config.configuration)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=OctopusEnergyTariff)
