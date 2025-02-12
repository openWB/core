#!/usr/bin/env python3
import logging

from modules.electricity_tariffs.octopusenergy.config import OctopusEnergyTariffConfiguration, OctopusEnergyTariff
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


def build_tariff_state(data) -> Dict[str, float]:
    current_time = datetime.now(timezone.utc)
    prices: Dict[str, float] = {}

    for hour in range(24):
        hour_time = current_time + timedelta(hours=hour)
        for agreement in data['account']['property']['electricityMalos'][0]['agreements']:
            valid_from = datetime.fromisoformat(agreement['validFrom'].replace('Z', '+00:00'))
            valid_to = datetime.fromisoformat(agreement['validTo'].replace('Z', '+00:00'))

            if valid_from <= hour_time <= valid_to:
                unit_rate_info = agreement['unitRateInformation']
                if unit_rate_info['__typename'] == 'SimpleProductUnitRateInformation':
                    rate = float(unit_rate_info['latestGrossUnitRateCentsPerKwh'])/100/1000
                    timestamp = str(int(hour_time.replace(minute=0, second=0, microsecond=0).timestamp()))
                    prices[timestamp] = rate
                elif unit_rate_info['__typename'] == 'TimeOfUseProductUnitRateInformation':
                    for rate_info in unit_rate_info['rates']:
                        active_from = datetime.strptime(
                            rate_info['timeslotActivationRules'][0]['activeFromTime'], '%H:%M:%S'
                        ).time()
                        active_to = datetime.strptime(
                            rate_info['timeslotActivationRules'][0]['activeToTime'], '%H:%M:%S'
                        ).time()
                        if active_from <= hour_time.time() < active_to or (active_to == datetime.min.time()
                                                                           and hour_time.time() >= active_from):
                            timestamp = str(int(hour_time.replace(minute=0, second=0, microsecond=0).timestamp()))
                            prices[timestamp] = float(rate_info['latestGrossUnitRateCentsPerKwh'])/100/1000
                            break

    sorted_prices = dict(sorted(prices.items()))
    return sorted_prices


def fetch(config: OctopusEnergyTariffConfiguration) -> TariffState:
    # request prices
    # call OctopusEnergyClient with the email and password from the config
    client = OctopusEnergyClient(email=config.email, password=config.password)
    property_data = client.get_property_ids(config.accountId)
    property_id = property_data["account"]["properties"][0]["id"]
    log.debug("Property IDs: %s", property_data)
    tariffs = client.get_smart_meter_usage(config.accountId, property_id)
    log.debug("Tariff Info: %s", tariffs)
    prices = build_tariff_state(tariffs)
    log.debug("Prices: %s", prices)

    return TariffState(prices=prices)


def create_electricity_tariff(config: OctopusEnergyTariff):
    def updater():
        return fetch(config.configuration)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=OctopusEnergyTariff)
